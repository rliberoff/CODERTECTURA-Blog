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
