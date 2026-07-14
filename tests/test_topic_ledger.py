import sys
from pathlib import Path

import pytest
import yaml


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "automation" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import topic_ledger as ledger  # noqa: E402


def _write_candidate(path: Path) -> None:
    document = {
        "id": "foundry-agent-observability",
        "title": "Observability for Microsoft Foundry agents",
        "slug": "foundry-agent-observability",
        "status": "candidate",
        "source": "https://learn.microsoft.com/azure/ai-foundry/agents/concepts/tracing",
        "discovered_at": "2026-07-14T08:00:00+00:00",
        "similarity": {
            "max_score": 0.31,
            "closest_match": "azure-observability",
            "threshold": 0.82,
        },
        "sources": [
            {
                "url": "https://learn.microsoft.com/azure/ai-foundry/agents/concepts/tracing",
                "title": "Trace agents",
                "published_date": "2026-07-10",
                "host": "learn.microsoft.com",
                "kind": "primary",
            }
        ],
        "pr_url": None,
    }
    path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def test_topic_moves_from_candidate_to_published_with_article_trace(tmp_path: Path) -> None:
    source = tmp_path / "candidate.yaml"
    topics_dir = tmp_path / "automation" / "topics"
    _write_candidate(source)

    topic_file = ledger.stage_topic_for_review(
        source,
        topics_dir,
        topic_id="foundry-agent-observability",
        article_slug="observabilidad-agentes-microsoft-foundry",
        article_path=(
            "content/posts/2026-07-14-observabilidad-agentes-microsoft-foundry.md"
        ),
        at="2026-07-14T09:00:00+00:00",
    )

    in_review = yaml.safe_load(topic_file.read_text(encoding="utf-8"))
    assert in_review["status"] == "in_review"
    assert [entry["status"] for entry in in_review["status_history"]] == [
        "candidate",
        "in_review",
    ]
    assert in_review["slug"] == "observabilidad-agentes-microsoft-foundry"
    assert in_review["article_path"].endswith(
        "2026-07-14-observabilidad-agentes-microsoft-foundry.md"
    )

    pr_url = "https://github.com/rliberoff/CODERTECTURA-Blog/pull/42"
    ledger.update_topic_status(
        topic_file,
        "published",
        at="2026-07-14T10:00:00+00:00",
        pr_url=pr_url,
    )

    published = yaml.safe_load(topic_file.read_text(encoding="utf-8"))
    assert published["status"] == "published"
    assert published["pr_url"] == pr_url
    assert [entry["status"] for entry in published["status_history"]] == [
        "candidate",
        "in_review",
        "published",
    ]

    ledger.update_topic_status(topic_file, "published", pr_url=pr_url)
    unchanged = yaml.safe_load(topic_file.read_text(encoding="utf-8"))
    assert unchanged["status_history"] == published["status_history"]


def test_stage_review_rejects_a_topic_id_that_can_escape_the_ledger(tmp_path: Path) -> None:
    source = tmp_path / "candidate.yaml"
    topics_dir = tmp_path / "automation" / "topics"
    _write_candidate(source)

    with pytest.raises(ledger.LedgerError, match="invalid topic id"):
        ledger.stage_topic_for_review(
            source,
            topics_dir,
            topic_id="../outside",
            article_slug="observabilidad-agentes-microsoft-foundry",
            article_path=(
                "content/posts/2026-07-14-observabilidad-agentes-microsoft-foundry.md"
            ),
        )

    assert not topics_dir.exists()


def test_topic_cannot_skip_directly_from_candidate_to_published() -> None:
    document = {"status": "candidate"}

    with pytest.raises(ledger.LedgerError, match="candidate -> published"):
        ledger.transition_topic(document, "published")


def test_published_topic_must_reference_a_post_in_the_approved_pr(tmp_path: Path) -> None:
    source = tmp_path / "candidate.yaml"
    topics_dir = tmp_path / "automation" / "topics"
    _write_candidate(source)
    topic_file = ledger.stage_topic_for_review(
        source,
        topics_dir,
        topic_id="foundry-agent-observability",
        article_slug="observabilidad-agentes-microsoft-foundry",
        article_path=(
            "content/posts/2026-07-14-observabilidad-agentes-microsoft-foundry.md"
        ),
        at="2026-07-14T09:00:00+00:00",
    )

    with pytest.raises(ledger.LedgerError, match="not part of the approved pull request"):
        ledger.update_topic_status(
            topic_file,
            "published",
            allowed_article_paths={"content/posts/2026-07-14-another-post.md"},
        )


def test_staging_an_existing_review_preserves_its_history(tmp_path: Path) -> None:
    source = tmp_path / "candidate.yaml"
    topics_dir = tmp_path / "automation" / "topics"
    _write_candidate(source)
    topic_file = ledger.stage_topic_for_review(
        source,
        topics_dir,
        topic_id="foundry-agent-observability",
        article_slug="observabilidad-agentes-microsoft-foundry",
        article_path=(
            "content/posts/2026-07-14-observabilidad-agentes-microsoft-foundry.md"
        ),
        at="2026-07-14T09:00:00+00:00",
    )
    original = yaml.safe_load(topic_file.read_text(encoding="utf-8"))

    ledger.stage_topic_for_review(
        topic_file,
        topics_dir,
        topic_id="foundry-agent-observability",
        article_slug="observabilidad-agentes-microsoft-foundry",
        article_path=(
            "content/posts/2026-07-14-observabilidad-agentes-microsoft-foundry.md"
        ),
        at="2026-07-15T09:00:00+00:00",
    )

    rerun = yaml.safe_load(topic_file.read_text(encoding="utf-8"))
    assert rerun["status_history"] == original["status_history"]


def test_prepare_candidate_build_derives_topic_and_sources(tmp_path: Path) -> None:
    topic_file = tmp_path / "candidate.yaml"
    topic_text_file = tmp_path / "topic.txt"
    sources_file = tmp_path / "sources.json"
    _write_candidate(topic_file)

    topic_id = ledger.prepare_candidate_build(
        topic_file,
        topic_text_file,
        sources_file,
    )

    assert topic_id == "foundry-agent-observability"
    assert topic_text_file.read_text(encoding="utf-8") == (
        "Observability for Microsoft Foundry agents"
    )
    sources = yaml.safe_load(sources_file.read_text(encoding="utf-8"))
    assert sources[0]["kind"] == "primary"