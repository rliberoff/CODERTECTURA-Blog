# Tony History

## Seed Context — 2026-06-10

- Project: CODERTECTURA-Blog.
- Owner: Rodrigo Liberoff.
- Goal: rebuild the blog with Hugo as a modern headless/static blog.
- Must preserve existing Markdown articles, image assets, and the current logo.
- Desired UI: modern look and feel with parallax, scroll reveal, responsive UX.
- Automation goal: GitHub Actions weekly AI-generated articles about Microsoft, AI, Microsoft Agent Framework, Microsoft Foundry, and related libraries.
- AI goal: use Microsoft Foundry models for both article text and generated images.


## Cross-agent update — 2026-06-24

- **Deferred design call — open-PR dedup (PENDING):** The Tavily weekly discovery pipeline defers fuller open-PR deduplication to Tony. Risk: unmerged weekly draft PRs can duplicate topics because the discovery ledger is ephemeral per run and dedup currently relies only on committed draft posts. Interim mitigation in force: "merge or close the weekly PRs before the next Monday run." Pending: a durable cross-run / open-PR dedup design. Source: 2026-06-24 Tavily discovery session. See `decisions.md` → 2026-06-24 entry (decision #6).
