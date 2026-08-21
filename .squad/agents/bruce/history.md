# Bruce History

## Seed Context — 2026-06-10

- Project: CODERTECTURA-Blog.
- Owner: Rodrigo Liberoff.
- Automation goal: weekly GitHub Actions generation of articles about Microsoft, AI, Microsoft Agent Framework, Microsoft Foundry, and related libraries.
- AI goal: use Microsoft Foundry models for article text and image generation.
- Constraints: secure secrets, reviewable workflow, no hardcoded credentials.


## Cross-agent update — 2026-06-23

- **Model selection locked for MVP** — `MAI-Image-2.5` (image) + `GPT-5.4-mini` (text, single-tier; no premium cascade).
- **ACTION (before Phase 0):** verify regional availability, `api-version` and pricing of BOTH models in Azure AI Foundry. Names/prices are Rodrigo's choice — confirm against official Foundry pages.
- Source: AI article pipeline design session (Rodrigo approvals). See `decisions.md` → 2026-06-23 entry.


## Cross-agent update — 2026-06-30

- **Standing convention for the AI pipeline: process in ENGLISH, publish in SPANISH (Spain).** All AI *processing* prompts in `discover_topics.py` and `generate_article.py` are now English; every reader-facing output (title, description, tags, categories, body, image alt/caption) stays Spanish; `image_prompt`/`prompt_en` remain English. Single pass (Option A) — no translation step.
- **`PROMPT_VERSION` bumped 2026-06-26.1 → 2026-06-30.1** in `generate_article.py`.
- Status: Bruce implemented; Natasha APPROVE; Rai 🟢 GREEN; 70 tests pass; working tree only — not committed. See `decisions.md` → 2026-06-30 entry.


## 2026-08-21 — Code-examples policy audit (read-only)

Audited the AI article pipeline (discover_topics.py, generate_article.py, topic_ledger.py, topic YAML schema, ai-article-build.yml) for Rodrigo's directive: technical posts need real, testable code examples; business posts exempt. Found no classification or enforcement exists. My 4-part recommendation is on record in decisions.md (2026-08-21 entry): `article_type` schema field, conditional `TECHNICAL_CODE_REQUIREMENT` prompt block, deterministic code-validation gate, discovery bias toward technical topics. Implementation PENDING Rodrigo's go-ahead — do not start without it.


## 2026-08-21 — Code-examples plan implemented (APPROVED)

- Implemented Rodrigo-approved 4-part plan across 8 files: `article_type` enum fail-closed → business in `discover_topics.py` (+ HANDS-ON PRIORITY 2/3 technical, technical-first stable ranking before trim, persisted `area` + `code_example_ideas`); `topic_ledger.py` `prepare_candidate_build` returns `{topic_id, article_type}` dict (+ `--code-ideas-file`); `generate_article.py` `TECHNICAL_CODE_REQUIREMENT` injected only for technical + deterministic `validate_technical_code` gate (≥2 tagged fences + placeholder scan, fail-hard) + `ai.article_type` front matter + `PROMPT_VERSION` 2026-08-21.1; `_example.yaml` + `automation/README.md` docs; `ai-article-build.yml` env plumbing; +20 tests.
- Natasha reviewed and APPROVED (added 2 regression tests; final 175 passed, 0 failed).
- Accepted low-severity risks (all fail closed): indented-block placeholder-scan gap; `placeholder=` HTML false-positive potential; topic_ledger exact-match vs lowercase-normalise enum inconsistency.
- Remember: `prepare_candidate_build` callers must now handle the dict return shape. Working tree only — not committed.
