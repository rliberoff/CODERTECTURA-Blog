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
