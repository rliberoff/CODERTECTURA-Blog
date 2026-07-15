---
name: blog-to-linkedin-article
description: Draft and publish a CODERTECTURA blog post as a native LinkedIn Article, preserving its cover, body structure, code, links, images, and captions. Resolves "latest post" automatically, extracts the canonical Hugo DOM, prepares the LinkedIn article and share teaser through the Claude in Chrome extension, audits the result, and stops for explicit confirmation at Publish. Use whenever the user asks to publish, republish, cross-post, or share a blog post or URL on LinkedIn as an Article.
---

# Blog post to LinkedIn Article

Draft one CODERTECTURA post as a native LinkedIn Article, including its cover, text, formatting, links, code, body images, and captions. LinkedIn has no supported Article publishing API, so use the browser session. Drafting is reversible; publishing is not.

Read `references/editor-scripts.md` before opening the editor. It contains the extraction, paste, image-transfer, placement, caption, cover, and audit scripts used by this workflow.

## Operating rules

- Ask no preference questions when a deterministic default exists.
- Keep the article body verbatim by default. Do not invent, summarize, translate, or rewrite technical claims.
- Keep code blocks inline. Do not ask whether to include them.
- Do not ask the user to confirm a title found in the RSS feed or canonical page.
- Pause only when authentication is required, source content is genuinely ambiguous after the recovery steps, or the irreversible Publish action needs confirmation.
- Never click Publish without explicit approval in the current chat. A previous approval is not reusable.
- Process one article per run.

## Prerequisites

1. Load the Chrome tools in one ToolSearch call: `tabs_context_mcp, navigate, computer, read_page, find, get_page_text, tabs_create_mcp, javascript_tool, browser_batch`.
2. Verify that the Claude in Chrome extension is connected.
3. Verify that LinkedIn is authenticated when first navigating there. If a login or challenge appears, pause and ask the user to complete it in the browser.

## Step 1 - Resolve the source

When the user provides a URL, use it. When the user says "my latest post" or omits the URL:

1. Fetch `https://codertectura.com/index.xml`.
2. Select the first RSS `item` whose URL path starts with `/posts/`.
3. Use the item's `link`; do not derive a permalink from the Markdown filename. Hugo uses the front matter `slug`, which can differ from the filename.
4. Navigate the browser to that URL and wait for redirects to finish. Use `link[rel="canonical"]` when present; otherwise use the final `location.href` unchanged, including its hostname and trailing slash.
5. Report the resolved title as a progress update and continue without requesting confirmation.

If the source returns an empty shell, use the browser DOM. If the canonical URL returns an error, retry once with the RSS URL. Ask the user only if both fail.

## Step 2 - Extract the Hugo article

The deployed Hugo DOM is the source of truth. Do not reconstruct content from Markdown, RSS descriptions, filenames, image folders, or visual screenshots.

For CODERTECTURA, use these selectors:

- Title: `article.post .post__header h1`
- Body root: `article.post .post__content`
- Cover: the URL in the computed `background-image` of `.post__header-bg`
- Cover fallbacks: `meta[property="og:image"]`, then `meta[name="twitter:image"]`, then the first body image. If none exists, draft the article without a cover.
- Body images: `.post__content img[src]`, in DOM order. Resolve the literal `src` attribute against the final page URL; do not depend on `currentSrc`, because off-screen lazy images can leave it empty.
- Figure caption: closest `figure.content-figure > figcaption`
- Gallery: `figure.content-gallery`; flatten its grid images in order and attach the gallery caption to the first image
- Notices and republished banners: `aside.notice`
- Embedded media: `.responsive-embed iframe`, `.content-video video`, and `.content-video iframe`

Run `extractCodertecturaArticle()` from the scripts reference. It must return a manifest containing:

- Effective canonical URL, language, exact title, sanitized body HTML, and attribution HTML
- Cover URL
- Ordered media entries with stable IDs, absolute URLs, file names, captions, alt text, and marker text
- A source snapshot with the original body selector and structural counts before conversion
- Expected counts for headings, lists, blockquotes, code blocks, links, markers, and media

The extraction script applies these deterministic conversions:

- Replace every body image with a unique visible marker such as `[[LI_MEDIA_001]]`. Never locate an image by nearby prose.
- Flatten galleries into consecutive image markers. Keep the gallery caption on the first image only.
- Convert `aside.notice` to `blockquote`, preserving its title, body, links, and position.
- Convert an iframe or video to a linked paragraph at the same position. If a local poster exists, insert the poster as an image before the link.
- Keep `p`, `h2`, `h3`, `strong`, `em`, `a`, `ul`, `ol`, `li`, `blockquote`, and `pre > code`.
- Convert relative `href` and media URLs with `new URL(value, canonicalUrl).href`.
- Remove navigation, metadata, sharing controls, comments, scripts, styles, SVG icons, lightbox wrappers, and presentation-only attributes.
- Use LinkedIn's native caption field only for link-free captions of at most 250 characters. If a caption contains one or more links, or exceeds 250 characters, leave the native caption empty and retain the complete rich caption as an emphasized paragraph immediately after the image.

ALWAYS append the follolwing attribution paragraph at the end: *Publicado originalmente en [CODERTECTURA](canonical URL).*

- When `aside.notice--republished` exists, preserve that notice and use "Esta versión se publicó en CODERTECTURA" instead of claiming original publication.

Do not rewrite the opening or add a closing question unless the user explicitly requested adaptation. This conservative default removes an approval round trip and avoids changing the author's meaning.

### Generic interpretation rules

- Derive every structural count from the current live body. Never expect a fixed number of headings, paragraphs, lists, links, figures, or images.
- Treat zero counts as valid. An article may omit code, quotes, tables, notices, galleries, embeds, captions, or body images.
- Preserve the order of direct and nested body nodes as they appear in `.post__content`; do not infer order from filenames, numbering, visual position, or nearby text.
- Treat canonical and social metadata as optional. Use the final page URL and computed header background when those elements are absent.
- Treat a dedicated cover as optional. Reuse the first body image when no header or social cover exists; if the article has no images, do not invent a cover or block publication.
- Read image URLs from `src` and resolve them against the effective page URL. Lazy-loading state and an empty `currentSrc` do not mean that an image is missing.
- Treat classes such as `content-figure--lightbox` as presentation only. Extract the semantic image, alt text, caption, and caption links without carrying the lightbox wrapper into LinkedIn.
- Preserve all caption links as clickable body links regardless of their domain, label, position, or number. Keep the complete caption around those links so their original context is not inferred or rewritten.
- Use each article's generated manifest as its own expected contract for the LinkedIn audit. Never compare one article with values captured from another article.

## Step 3 - Run source preflight

Before touching LinkedIn, validate the manifest in one DOM call:

- Title and body are non-empty.
- The canonical URL is an HTTP or HTTPS URL.
- Cover URL and source are either both present or both absent. When present, the cover resolves to a valid image; when absent, the article contains no usable cover fallback.
- Every body image has a unique ID, marker, absolute URL, and file name.
- Marker count in `bodyHtml` equals media count.
- Every image URL is same-origin for CODERTECTURA and returns an image MIME type.
- Expected structural counts are recorded.
- The source snapshot identifies `.content.post__content` and its original direct-child, heading, list, link, figure, and image counts.
- No site chrome, comment heading, cookie text, or share links are present.

Retry extraction once after a page reload if preflight fails. If only the cover is missing, inspect the two metadata fallbacks once. Stop and explain the exact missing invariant rather than guessing a path.

## Step 4 - Draft the text once

1. Navigate to `https://www.linkedin.com/article/new/`. Fallback: `linkedin.com/feed/` → "Write article".
2. Click the Title field and type the title with the computer tool.
3. Capture the resulting editor URL after LinkedIn creates the draft. Reuse this exact URL for image transfer.
4. Insert the complete `bodyHtml` in one synthetic HTML paste into `div.ProseMirror[contenteditable="true"]`.
5. Start the HTML with `<p></p>` so ProseMirror's first-block merge is absorbed.
6. Run `auditLinkedInDraft(manifest)` immediately.

The editor does not understand Markdown text. Paste HTML only. LinkedIn may normalize both `h2` and `h3` to `h3.article-editor-heading`, so compare total heading count rather than heading levels.

If the first audit finds a merged first block, empty leading paragraph, or one demoted heading, use the targeted repair scripts. Never clear and repaste a non-empty draft unless the user explicitly asks to start over.

## Step 5 - Transfer and place images

LinkedIn's CSP blocks external image fetches and remote images in pasted HTML. Use the hash-transfer functions from the scripts reference in the same tab:

1. Wait until the draft reports saved before leaving LinkedIn.
2. Navigate the same tab to the canonical CODERTECTURA URL.
3. Fetch the cover and body images from their absolute manifest URLs.
4. Normalize the remaining images with `prepareNextImagePayload()`. Keep small files unchanged; resize and recompress large raster images to stay within the hash budget. Preserve a small GIF; convert an oversized GIF to a static JPEG preview.
5. Let the function fill one encoded payload below 1.2 MB and return `includedNames` plus `remainingNames`. Do not estimate batches manually.
6. Navigate to the exact saved editor URL with the prepared hash. The first JavaScript call after navigation MUST be `hydrateTransferredImageFiles()` so it hydrates `window.__files` and strips the hash with `history.replaceState` in that same call. Do not run another browser, DOM, or JavaScript action first because tool responses can echo the complete base64 URL and overflow the tab context.
7. Insert each included body image with `insertImageAtMarker(marker, fileName, captionText)`, one at a time and in manifest order.
8. After each upload, verify that the figure count increased by one and that the marker was removed. A CDP timeout from `insertImageAtMarker()` is an indeterminate result, not proof of failure: wait outside the browser tool, re-query the editor, and run `recoverTimedOutImageInsertion(marker)` before any retry. If the figure exists, do not upload it again; relocate it to the recorded marker position when needed, then verify its caption. Retry once only when no figure was created and the marker still exists.
9. If `remainingNames` is non-empty, return to the canonical post, rerun extraction, and prepare only those remaining media. Repeat until none remain.
10. If the manifest has a cover URL, upload it in its own final payload. Run `openArticleCoverCrop(fileName)` and verify the `crop-ready` state first; then run `confirmArticleCoverCrop()` as a separate action and require the `applied` state. A timeout waiting for the final cover image is also indeterminate: inspect `getArticleCoverUploadState()` before retrying. If the crop dialog remains open, click its enabled Next button once; if the cover is already applied, continue without uploading again. Restore every patched browser prototype in a `finally` path. Otherwise skip cover upload.

Marker-based placement is mandatory. It works for images at the beginning, adjacent figures, repeated prose, and galleries, all of which make nearby-text anchoring unreliable.

## Step 6 - Final audit and recovery

Run one manifest-aware DOM audit and require all of the following:

- Exact title
- Expected total headings, lists, blockquotes, code blocks, and links
- Figure count equal to body media count
- Captions equal to their planned plain text
- No `[[LI_MEDIA_` markers
- Final attribution present and linked to the canonical URL
- Cover presence matches the manifest: present when a dedicated or fallback cover was resolved, absent otherwise
- No empty paragraphs except a transient editor placeholder
- Draft saved indicator present

Repair only the failed element. Re-query the live DOM before one retry. Do not repeat successful uploads, repaste the body, or restart the article. If the second attempt fails, stop with the failed invariant, expected value, and observed value.

Take one screenshot at the top only after the DOM audit passes.

## Step 7 - Prepare the publish dialog

1. Click "Next" in the editor header. LinkedIn shows the share/publish step: a post composer where the article will be attached.
2. Fill the share box with a warm teaser in the article language: two to four conversational, friendly, first-person sentences stating the hook and what the reader will get.
3. Add three to five short, common hashtags on a separate line. Prefer tags already represented by the article title, categories, or tags. Avoid long compound hashtags.
4. ALWAYS add the `#MVPBuzz` hashtag.
5. Show the exact teaser and hashtags in chat and state that the dialog is ready.
6. Stop before Publish and request explicit confirmation. If the user says "publish" in the current chat, click Publish once and verify the published confirmation or resulting article URL.

If the user asked for edits to the teaser, edit in the dialog rather than starting over.

## Speed and stability rules

- Prefer DOM checks over screenshots.
- Use the canonical page DOM, never RSS `description`, as article content.
- Carry one manifest through extraction, paste, upload, and final audit.
- Batch read-only checks; keep image uploads sequential because each changes editor state.
- Allow at most one targeted retry per failed action.
- Batch predictable steps with browser_batch.
- After hash navigation, wait outside the browser tool so tool output does not echo the large URL.
- Make `hydrateTransferredImageFiles()` the first JavaScript call after every hash navigation. Do not inspect the tab or editor before that call removes the payload URL.
- Treat a browser or CDP timeout during an upload as unknown completion state. Inspect the live DOM and recover placement before deciding whether a retry is safe.
- Treat cover selection, crop readiness, and final application as separate states. Never infer that the upload failed only because the final cover selector timed out.
- Do not use `window.open`, `target=_blank`, or popups to bridge tabs.
- Do not close tabs mid-flow.
- Remote `<img src>` in pasted HTML is rejected by the editor schema; data transfer is genuinely required.
- Never use `fetch()` from the LinkedIn tab for external URLs or data URLs; its CSP blocks both.
- Restore patched browser APIs even when the cover upload fails.
- Do not publish more than one assisted article per run.
