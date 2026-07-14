from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


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

    assert "automation\\/topics\\/" in workflow
    assert "automation/scripts/topic_ledger.py" in workflow
    assert '--status "published"' in workflow
    assert "ref: ${{ github.event.review.commit_id }}" in workflow
    assert "--force-with-lease=" in workflow
    assert "--article-paths-file" in workflow
    assert "git add -- content/posts automation/topics" in workflow
    assert "uses: actions/create-github-app-token@v1" in workflow
    assert "token: ${{ steps.app-token.outputs.token }}" in workflow