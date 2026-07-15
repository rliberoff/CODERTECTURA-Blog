import os
from pathlib import Path
import subprocess
import sys
from textwrap import dedent

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def _publication_script(workflow: str) -> str:
    script_start = workflow.index("          python - <<'PY'\n") + len("          python - <<'PY'\n")
    script_end = workflow.index("\n          PY", script_start)
    return dedent(workflow[script_start:script_end])


def test_weekly_workflow_transports_one_complete_candidate() -> None:
    workflow = _workflow("ai-article-weekly.yml")

    assert "matrix: ${{ steps.discover.outputs.matrix }}" in workflow
    assert "count: ${{ steps.discover.outputs.count }}" in workflow
    assert "candidate_b64: ${{ matrix.candidate_b64 }}" in workflow
    assert "topic_file_b64" not in workflow
    assert "sources_file_b64" not in workflow
    assert "python - <<'PY'" not in workflow
    assert 'REQUIRE_EMBEDDINGS: "true"' in workflow
    assert "discovery-debug.json" in workflow
    assert 'pulls/${pr_number}/files' in workflow
    assert "git ls-tree -r --name-only FETCH_HEAD automation/topics" not in workflow
    assert "declare -A loaded_topics" in workflow


def test_build_workflow_derives_everything_from_the_candidate() -> None:
    workflow = _workflow("ai-article-build.yml")

    assert "candidate_b64:" in workflow
    assert "topic_file_b64:" not in workflow
    assert "sources_file_b64:" not in workflow
    assert "topic_ledger.py prepare-build" in workflow
    assert "ARTICLE_TOPIC_FILE:" in workflow
    assert "SOURCES_FILE:" in workflow
    assert "${{ steps.ledger.outputs.path }}" in workflow
    assert "steps.create-pr.outputs.pull-request-url" not in workflow
    assert "topic_ledger.py set-pr" not in workflow
    assert "bot/ai-article-${TOPIC_ID}" in workflow
    assert "GH_APP_INSTALLATION_ID" not in workflow


def test_approval_workflow_publishes_the_topic_ledger() -> None:
    workflow = _workflow("auto-publish-after-codeowner-approval.yml")
    publication_script = _publication_script(workflow)

    assert "automation\\/topics\\/" in workflow
    assert "automation/scripts/topic_ledger.py" in workflow
    assert '--status "published"' in workflow
    assert "ref: ${{ github.event.review.commit_id }}" in workflow
    assert "--force-with-lease=" in workflow
    assert "--article-paths-file" in workflow
    assert "git add -- content/posts automation/topics" in workflow
    assert "uses: actions/create-github-app-token@v1" in workflow
    assert "token: ${{ steps.app-token.outputs.token }}" in workflow
    assert "REVIEWED_AT: ${{ github.event.review.submitted_at }}" in workflow
    assert 'data["date"] = reviewed_at' in workflow
    assert "datetime.datetime.now(datetime.timezone.utc)" not in workflow
    compile(publication_script, "auto-publish-front-matter", "exec")


def test_approval_workflow_uses_review_time_as_publication_date(tmp_path: Path) -> None:
    post_path = tmp_path / "content" / "posts" / "reviewed-article.md"
    post_path.parent.mkdir(parents=True)
    post_path.write_text(
        """---
title: Reviewed article
date: '2026-07-01T10:07:38Z'
draft: true
ai:
  review_status: pending
---
Article body.
""",
        encoding="utf-8",
    )
    reviewed_at = "2026-07-15T14:32:10Z"
    env = os.environ | {
        "TARGET_FILES": str(post_path),
        "REVIEWER": "rliberoff",
        "REVIEWED_AT": reviewed_at,
    }

    subprocess.run(
        [sys.executable, "-c", _publication_script(_workflow("auto-publish-after-codeowner-approval.yml"))],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    raw = post_path.read_text(encoding="utf-8")
    front_matter = yaml.safe_load(raw.removeprefix("---\n").split("\n---\n", 1)[0])

    assert front_matter["date"] == reviewed_at
    assert front_matter["draft"] is False
    assert front_matter["ai"]["review_status"] == "approved"
    assert front_matter["ai"]["reviewed_by"] == "rliberoff"
    assert front_matter["ai"]["reviewed_at"] == reviewed_at
    assert raw.endswith("Article body.\n")