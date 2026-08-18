#!/usr/bin/env python3
"""Create a revised cover-image prompt for an article already in a PR.

This script powers the "refresh cover only" workflow: it reads the current
article draft plus a short editorial change request, asks the text model to
rewrite ONLY the cover brief, and writes that prompt to ``IMAGE_PROMPT_FILE``
for ``generate_image.py``. No article text, body images or ledger files are
changed here.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml

from _cover_style import COVER_BRIEF_SPEC
from _foundry import FoundryChatClient, FoundryError

MIN_COVER_PROMPT_CHARS = 80
MAX_COVER_PROMPT_CHARS = 2400
MAX_ARTICLE_EXCERPT_CHARS = 2000
MAX_CHANGE_REQUEST_CHARS = 600
DEFAULT_TIMEOUT = 180.0
DEFAULT_MAX_COMPLETION_TOKENS = 1200

SYSTEM_PROMPT = f"""\
You revise ONLY the cover-image brief for an existing CODERTECTURA article draft.

Your task:
- Keep the article's thesis, audience and concrete technologies recognisable.
- Apply the user's revision request as a visual adjustment to the cover concept.
- Improve the brief, do not explain your reasoning.
- Return ONLY a JSON object with the single key "image_prompt".

The value of "image_prompt" must be {COVER_BRIEF_SPEC}
Do not add Markdown fences or extra keys.
"""


def fail(message: str) -> "None":
    """Print a secret-free error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _read_text_file(path: str, *, label: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"could not read {label} ({path}): {exc}")


def read_change_request() -> str:
    """Return the editorial cover-change request from file or env."""
    brief_file = os.environ.get("COVER_REVIEW_BRIEF_FILE", "").strip()
    if brief_file:
        text = _read_text_file(brief_file, label="COVER_REVIEW_BRIEF_FILE").strip()
        if text:
            return text[:MAX_CHANGE_REQUEST_CHARS]

    brief = os.environ.get("COVER_REVIEW_BRIEF", "").strip()
    if brief:
        return brief[:MAX_CHANGE_REQUEST_CHARS]

    fail("no cover review brief provided (set COVER_REVIEW_BRIEF_FILE or COVER_REVIEW_BRIEF)")


def split_front_matter(text: str) -> "tuple[dict, str]":
    """Return ``(front_matter, body)`` from a Hugo-style Markdown document."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + len("\n---\n") :]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}, text
    return (data if isinstance(data, dict) else {}, body)


def plain_text_excerpt(markdown: str, *, max_chars: int = MAX_ARTICLE_EXCERPT_CHARS) -> str:
    """Reduce Markdown to a compact plain-text excerpt for prompt grounding."""
    text = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?m)^\s*(?:[-+*]|\d+[.)])\s+", "", text)
    text = re.sub(r"\{\{img:[^}]+\}\}", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def build_user_prompt(front_matter: dict, body_markdown: str, change_request: str) -> str:
    """Assemble the grounded prompt sent to the text model."""
    title = str(front_matter.get("title") or "").strip()
    if not title:
        fail("article front matter must contain a non-empty title")

    description = str(front_matter.get("description") or "").strip()
    tags = front_matter.get("tags")
    categories = front_matter.get("categories")
    tags_text = ", ".join(str(tag).strip() for tag in tags) if isinstance(tags, list) else ""
    categories_text = (
        ", ".join(str(category).strip() for category in categories)
        if isinstance(categories, list)
        else ""
    )
    excerpt = plain_text_excerpt(body_markdown)

    parts = [
        "Revise the cover brief for this existing article draft.",
        f"Title: {title}",
    ]
    if description:
        parts.append(f"Description: {description}")
    if tags_text:
        parts.append(f"Tags: {tags_text}")
    if categories_text:
        parts.append(f"Categories: {categories_text}")
    if excerpt:
        parts.append(f"Article excerpt: {excerpt}")
    parts.append(f"Requested cover changes: {change_request}")
    parts.append("Return only the JSON object.")
    return "\n".join(parts)


def parse_image_prompt(content: object) -> str:
    """Extract and validate ``image_prompt`` from the model's JSON reply."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("the model returned empty content")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("the model did not return valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("the model JSON was not an object")
    prompt = payload.get("image_prompt")
    if not isinstance(prompt, str):
        raise ValueError("the model JSON did not contain a string 'image_prompt'")
    prompt = prompt.strip()
    if len(prompt) < MIN_COVER_PROMPT_CHARS:
        raise ValueError("the revised image_prompt was unexpectedly short")
    if len(prompt) > MAX_COVER_PROMPT_CHARS:
        raise ValueError("the revised image_prompt exceeded the allowed length")
    return prompt


def _write_debug_json(path: str, payload: dict) -> None:
    """Persist a debug JSON payload (best effort, never raises)."""
    if not path:
        return
    try:
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Wrote cover-refresh debug trace: {path}")
    except OSError as exc:
        print(
            f"WARNING: could not write COVER_PROMPT_DEBUG_FILE ({path}): {exc}",
            file=sys.stderr,
        )


def _env_truthy(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _emit_trace(payload: dict) -> None:
    print("::group::AI TRACE - cover refresh prompt")
    print("SYSTEM_PROMPT:")
    print(payload.get("system_prompt", ""))
    print("\nUSER_PROMPT:")
    print(payload.get("user_prompt", ""))
    print("::endgroup::")

    print("::group::AI TRACE - cover refresh summary")
    summary = {
        "article_path": payload.get("article_path"),
        "deployment": payload.get("deployment"),
        "change_request": payload.get("change_request"),
        "image_prompt": payload.get("image_prompt"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("::endgroup::")


def main() -> None:
    endpoint = os.environ.get("AOAI_ENDPOINT", "").strip()
    if not endpoint:
        fail("no Foundry endpoint provided (set AOAI_ENDPOINT)")

    deployment = (
        os.environ.get("AOAI_GENERATE_DEPLOYMENT", "").strip()
        or os.environ.get("AOAI_TEXT_DEPLOYMENT", "").strip()
    )
    if not deployment:
        fail("no text deployment provided (set AOAI_GENERATE_DEPLOYMENT or AOAI_TEXT_DEPLOYMENT)")

    token = os.environ.get("AOAI_TOKEN", "").strip()
    if not token:
        fail("no bearer token provided (set AOAI_TOKEN; never pass it on the command line)")

    article_path = os.environ.get("ARTICLE_PATH", "").strip()
    if not article_path:
        fail("no article path provided (set ARTICLE_PATH)")
    image_prompt_file = os.environ.get("IMAGE_PROMPT_FILE", "").strip()
    if not image_prompt_file:
        fail("no output path provided (set IMAGE_PROMPT_FILE)")

    try:
        timeout = float(os.environ.get("COVER_REVIEW_TIMEOUT", str(DEFAULT_TIMEOUT)))
    except ValueError:
        fail("COVER_REVIEW_TIMEOUT must be a number (seconds)")

    try:
        max_completion_tokens = int(
            os.environ.get(
                "COVER_REVIEW_MAX_COMPLETION_TOKENS",
                str(DEFAULT_MAX_COMPLETION_TOKENS),
            )
        )
    except ValueError:
        fail("COVER_REVIEW_MAX_COMPLETION_TOKENS must be an integer")

    change_request = read_change_request()
    article_text = _read_text_file(article_path, label="ARTICLE_PATH")
    front_matter, body_markdown = split_front_matter(article_text)
    user_prompt = build_user_prompt(front_matter, body_markdown, change_request)

    debug_payload = {
        "article_path": article_path,
        "deployment": deployment,
        "change_request": change_request,
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": user_prompt,
        "max_completion_tokens": max_completion_tokens,
    }

    client = FoundryChatClient(
        endpoint=endpoint,
        deployment=deployment,
        token=token,
        timeout=timeout,
    )
    try:
        response = client.complete(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=max_completion_tokens,
        )
    except FoundryError as exc:
        fail(str(exc))

    content = (response.get("message") or {}).get("content")
    try:
        image_prompt = parse_image_prompt(content)
    except ValueError as exc:
        fail(str(exc))

    out_path = Path(image_prompt_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(image_prompt, encoding="utf-8", newline="\n")

    debug_payload["image_prompt"] = image_prompt
    _write_debug_json(os.environ.get("COVER_PROMPT_DEBUG_FILE", "").strip(), debug_payload)
    if _env_truthy("COVER_PROMPT_TRACE_STDOUT", default=False):
        _emit_trace(debug_payload)

    print(f"Wrote revised cover prompt: {image_prompt_file}")


if __name__ == "__main__":
    main()
