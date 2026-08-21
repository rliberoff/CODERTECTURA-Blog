# Natasha History

## Seed Context — 2026-06-10

- Project: CODERTECTURA-Blog.
- Owner: Rodrigo Liberoff.
- Key constraints: preserve posts, preserve images, preserve logo.
- Quality targets: Hugo build reliability, link/image integrity, SEO, accessibility, and safe AI-content workflow.


## Cross-agent update — 2026-06-30

- **Standing convention for the AI pipeline: process in ENGLISH, publish in SPANISH (Spain).** All AI *processing* prompts in `discover_topics.py` and `generate_article.py` are now English; every reader-facing output (title, description, tags, categories, body, image alt/caption) stays Spanish; `image_prompt`/`prompt_en` remain English. Single pass (Option A) — no translation step.
- **`PROMPT_VERSION` bumped 2026-06-26.1 → 2026-06-30.1** in `generate_article.py` (Natasha's only source edit).
- Status: Bruce implemented; Natasha APPROVE; Rai 🟢 GREEN; `pytest tests/test_discover_topics.py tests/test_generate_article.py` → 70 passed; working tree only — not committed. See `decisions.md` → 2026-06-30 entry.


## 2026-08-21 — Team update: possible two-lock violation flagged (from Shuri)

Shuri's editorial review found the 2026-07-28 post has `draft:false` while `review_status:pending` — this may violate the 2026-06-23 TWO-LOCK publishing model (approved PR merge + `draft:false` + `ai.reviewed_by` required to render). Verify the post's front matter and review state; details in decisions.md 2026-08-21 entry.


## 2026-08-21 — Review of code-examples plan implementation (Bruce)

- Verdict: **APPROVE.** Verified `article_type` fail-closed at all 3 layers (discovery, ledger, generation); `validate_technical_code` gate not bypassable (`~~~` fences, indented blocks, fence-in-fence, CRLF); Spanish "todo" safe from TODO scan; workflow env names match; no placeholders; CODE_RUBRIC untouched. Added 2 regression tests. Final: 175 passed, 0 failed.
- Accepted risks logged (low severity, fail closed): indented-block placeholder-scan gap; `placeholder=` HTML false-positive potential; topic_ledger exact-match vs lowercase-normalise inconsistency.
- **STILL OPEN:** the 2026-07-28 post has `draft:false` with `review_status:pending` — possible TWO-LOCK (2026-06-23) violation. Awaiting Rodrigo's decision before acting.
