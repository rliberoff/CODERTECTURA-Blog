# Project Context

- **Project:** CODERTECTURA-Blog
- **Created:** 2026-06-10

## Core Context

Agent Rai initialized and ready for work.

## Recent Updates

📌 Team initialized on 2026-06-10

## Learnings

Initial setup complete.


## Cross-agent update — 2026-06-30

- **Standing convention for the AI pipeline: process in ENGLISH, publish in SPANISH (Spain).** All AI *processing* prompts in `discover_topics.py` and `generate_article.py` are now English; every reader-facing output (title, description, tags, categories, body, image alt/caption) stays Spanish; `image_prompt`/`prompt_en` remain English. Single pass (Option A) — no translation step.
- **RAI verdict: 🟢 GREEN** — all 7 prompt-injection/safety invariants intact across both scripts; no secrets exposed; fairness clean. Redacted entry appended to `.squad/rai/audit-trail.md`.
- **`PROMPT_VERSION` bumped 2026-06-26.1 → 2026-06-30.1** in `generate_article.py`. Status: working tree only — not committed. See `decisions.md` → 2026-06-30 entry.
