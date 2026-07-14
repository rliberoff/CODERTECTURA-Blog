#!/usr/bin/env python3
"""Validate and advance topic-ledger entries through the article workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import yaml

from _sources import sanitize_untrusted_text


TOPIC_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = TOPIC_ID_PATTERN
ALLOWED_TRANSITIONS = {
    "candidate": {"queued", "in_review", "rejected", "parked"},
    "queued": {"in_review", "rejected", "parked"},
    "in_review": {"published", "rejected", "parked"},
    "published": set(),
    "rejected": set(),
    "parked": {"queued"},
}


class LedgerError(ValueError):
    """Raised when a ledger entry or transition violates the contract."""


def _timestamp(value: str | None = None) -> str:
    if value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LedgerError(f"invalid ISO 8601 timestamp: {value}") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise LedgerError(f"timestamp must include a timezone: {value}")
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_topic_id(topic_id: str) -> str:
    if not TOPIC_ID_PATTERN.fullmatch(topic_id):
        raise LedgerError(f"invalid topic id: {topic_id}")
    return topic_id


def _validate_article_path(article_path: str) -> str:
    path = PurePosixPath(article_path)
    if (
        path.is_absolute()
        or ".." in path.parts
        or len(path.parts) != 3
        or path.parts[:2] != ("content", "posts")
        or path.suffix != ".md"
    ):
        raise LedgerError(f"invalid article path: {article_path}")
    return article_path


def _validate_pr_url(pr_url: str) -> str:
    parsed = urlsplit(pr_url)
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path:
        raise LedgerError(f"invalid pull request URL: {pr_url}")
    return pr_url


def load_topic(path: Path, *, expected_id: str | None = None) -> dict:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LedgerError(f"could not read topic file {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise LedgerError(f"topic file is not a YAML mapping: {path}")

    topic_id = document.get("id")
    if not isinstance(topic_id, str):
        raise LedgerError("topic id must be a string")
    _validate_topic_id(topic_id)
    if expected_id is not None and topic_id != _validate_topic_id(expected_id):
        raise LedgerError(f"topic id mismatch: expected {expected_id}, found {topic_id}")

    status = document.get("status")
    if status not in ALLOWED_TRANSITIONS:
        raise LedgerError(f"invalid topic status: {status}")
    return document


def write_topic(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    path.write_text(payload, encoding="utf-8", newline="\n")


def transition_topic(document: dict, status: str, *, at: str | None = None) -> None:
    if status not in ALLOWED_TRANSITIONS:
        raise LedgerError(f"invalid target status: {status}")

    current = document.get("status")
    if current not in ALLOWED_TRANSITIONS:
        raise LedgerError(f"invalid current status: {current}")
    if current == status:
        return
    if status not in ALLOWED_TRANSITIONS[current]:
        raise LedgerError(f"invalid topic transition: {current} -> {status}")

    changed_at = _timestamp(at)
    history = document.get("status_history")
    if not isinstance(history, list):
        history = []
    if not history:
        discovered_at = document.get("discovered_at")
        history.append(
            {
                "status": current,
                "at": discovered_at if isinstance(discovered_at, str) else changed_at,
            }
        )
    history.append({"status": status, "at": changed_at})
    document["status"] = status
    document["status_history"] = history


def stage_topic_for_review(
    source_file: Path,
    topics_dir: Path,
    *,
    topic_id: str,
    article_slug: str,
    article_path: str,
    at: str | None = None,
) -> Path:
    topic_id = _validate_topic_id(topic_id)
    if not SLUG_PATTERN.fullmatch(article_slug):
        raise LedgerError(f"invalid article slug: {article_slug}")
    article_path = _validate_article_path(article_path)
    document = load_topic(source_file, expected_id=topic_id)
    changed_at = _timestamp(at)

    if document["status"] in {"candidate", "queued"}:
        transition_topic(document, "in_review", at=changed_at)
    if document["status"] != "in_review":
        raise LedgerError(f"cannot stage topic from status {document['status']}")

    document["slug"] = article_slug
    document["article_path"] = article_path
    document.setdefault("pr_url", None)
    target = topics_dir / f"{topic_id}.yaml"
    write_topic(target, document)
    return target


def prepare_candidate_build(
    topic_file: Path,
    topic_text_file: Path,
    sources_file: Path,
) -> str:
    """Derive the article prompt and grounding sources from one ledger entry."""
    document = load_topic(topic_file)
    title = sanitize_untrusted_text(document.get("title"), max_length=300)
    if not title:
        raise LedgerError("topic title must be a non-empty string")
    notes = sanitize_untrusted_text(document.get("notes"), max_length=200)
    topic_text = f"{title}. Enfoque: {notes}" if notes else title
    sources = document.get("sources")
    if not isinstance(sources, list):
        sources = []

    topic_text_file.parent.mkdir(parents=True, exist_ok=True)
    sources_file.parent.mkdir(parents=True, exist_ok=True)
    topic_text_file.write_text(topic_text, encoding="utf-8", newline="\n")
    sources_file.write_text(
        json.dumps(sources, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return document["id"]


def update_topic_status(
    topic_file: Path,
    status: str,
    *,
    at: str | None = None,
    pr_url: str | None = None,
    allowed_article_paths: "set[str] | None" = None,
) -> None:
    document = load_topic(topic_file, expected_id=topic_file.stem)
    transition_topic(document, status, at=at)
    if pr_url:
        document["pr_url"] = _validate_pr_url(pr_url)
    if status == "published":
        article_path = document.get("article_path")
        if not isinstance(article_path, str):
            raise LedgerError("a published topic must reference article_path")
        article_path = _validate_article_path(article_path)
        if allowed_article_paths is not None and article_path not in allowed_article_paths:
            raise LedgerError(
                f"topic article_path is not part of the approved pull request: {article_path}"
            )
    write_topic(topic_file, document)


def _write_output(name: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stage = subparsers.add_parser("stage-review")
    stage.add_argument("--source-file", type=Path, required=True)
    stage.add_argument("--topics-dir", type=Path, required=True)
    stage.add_argument("--topic-id", required=True)
    stage.add_argument("--article-slug", required=True)
    stage.add_argument("--article-path", required=True)
    stage.add_argument("--at")

    prepare = subparsers.add_parser("prepare-build")
    prepare.add_argument("--topic-file", type=Path, required=True)
    prepare.add_argument("--topic-text-file", type=Path, required=True)
    prepare.add_argument("--sources-file", type=Path, required=True)

    update = subparsers.add_parser("update")
    update.add_argument("--topic-file", type=Path, required=True)
    update.add_argument("--status", choices=sorted(ALLOWED_TRANSITIONS), required=True)
    update.add_argument("--at")
    update.add_argument("--pr-url")
    update.add_argument("--article-paths-file", type=Path)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "stage-review":
            path = stage_topic_for_review(
                args.source_file,
                args.topics_dir,
                topic_id=args.topic_id,
                article_slug=args.article_slug,
                article_path=args.article_path,
                at=args.at,
            )
            _write_output("path", path.as_posix())
            print(f"Staged topic ledger for review: {path.as_posix()}")
        elif args.command == "prepare-build":
            topic_id = prepare_candidate_build(
                args.topic_file,
                args.topic_text_file,
                args.sources_file,
            )
            _write_output("topic_id", topic_id)
            _write_output("topic_file", args.topic_file.as_posix())
            _write_output("topic_text_file", args.topic_text_file.as_posix())
            _write_output("sources_file", args.sources_file.as_posix())
            print(f"Prepared candidate for article generation: {topic_id}")
        else:
            allowed_article_paths = None
            if args.article_paths_file is not None:
                allowed_article_paths = {
                    line.strip()
                    for line in args.article_paths_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                }
            update_topic_status(
                args.topic_file,
                args.status,
                at=args.at,
                pr_url=args.pr_url,
                allowed_article_paths=allowed_article_paths,
            )
            print(f"Updated topic ledger to {args.status}: {args.topic_file.as_posix()}")
    except LedgerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())