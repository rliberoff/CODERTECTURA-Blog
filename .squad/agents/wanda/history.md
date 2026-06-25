# Wanda History

## Seed Context — 2026-06-10

- Project: CODERTECTURA-Blog.
- Owner: Rodrigo Liberoff.
- Goal: modernize the blog using Hugo while preserving posts, images, and the current logo.
- Specific user directive: analyze the current page style before modernization and preserve the logo.
- Desired UI: modern technical-blog identity with parallax and scroll reveal.


## Cross-agent update — 2026-06-23

- **Cover-image model changed** from `gpt-image-1` to `MAI-Image-2.5`.
- **ACTION:** re-validate art direction, prompt template and the frozen negative-prompt against `MAI-Image-2.5` capabilities.
- Source: AI article pipeline design session (Rodrigo approvals). See `decisions.md` → 2026-06-23 entry.


## Cross-agent update — 2026-06-24

- **Optional follow-up — AI image style coherence:** The Tavily pipeline now generates an AI cover AND AI body images/diagrams per article, and may also embed real images extracted from allowlisted source articles. Suggested (non-blocking) follow-up: tune the AI image style / prompt templates for visual coherence across cover + body images — consistent palette, composition, and the technical-blog identity. Source: 2026-06-24 Tavily discovery session. See `decisions.md` → 2026-06-24 entry (decision #3).
