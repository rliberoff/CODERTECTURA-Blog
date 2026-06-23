# Squad Decisions

## Active Decisions

- **2026-06-10 — Hugo rebuild strategy:** Rebuild the blog as a custom in-repo Hugo site rather than adopting a third-party theme. Preserve existing Markdown posts, `/posts/<slug>` URLs where possible, `/images/...` asset paths, all existing images, and `images/logo.png` unchanged.
- **2026-06-10 — AI content publishing model:** Weekly Microsoft Foundry generation must create draft posts, generated images, metadata, and a pull request for human review. It must not auto-publish directly to the main branch.
- **2026-06-10 — Visual modernization constraint:** Modernize the look and feel with progressive parallax and scroll reveal, but preserve the current logo and keep motion accessible via `prefers-reduced-motion` support.
- **2026-06-10 — Hugo migration validation:** Hugo is installed locally under `.tools/hugo/` and ignored by Git. All 36 Jekyll posts have migrated Hugo counterparts under `content/posts/`; `_posts/` remains unchanged. `tools/validate_hugo_migration.py --warn-unmigrated` and `.tools/hugo/hugo.exe --gc --minify --destination public-hugo-preview` pass. Production cutover remains gated on staging/preview smoke tests.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
