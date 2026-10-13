---
name: blog-to-linkedin-article
description: Draft and publish a CODERTECTURA blog post as a native LinkedIn Article (usually as an edition of the CODERTECTURA newsletter), preserving its cover, body structure, code, links, images, and captions. Resolves "latest post" automatically, extracts the canonical Hugo DOM, rewrites tables as readable lists, marks inline code with single quotes, prepares the LinkedIn article and share teaser through the Claude in Chrome extension, audits the result, and stops for explicit confirmation at Publish. Use whenever the user asks to publish, republish, cross-post, or share a blog post or URL on LinkedIn as an Article or in the CODERTECTURA newsletter/list.
---

# Blog post to LinkedIn Article

Draft one CODERTECTURA post as a native LinkedIn Article, including its cover, text, formatting, links, code, body images, and captions. LinkedIn has no supported Article publishing API, so use the browser session. Drafting is reversible; publishing is not.

Read `references/editor-scripts.md` before opening the editor. It contains the extraction, table-rewrite, bundle-transfer, paste, image-placement, caption, cover, text-edit, link-repair, and audit scripts used by this workflow.

## Operating rules

- Ask no preference questions when a deterministic default exists.
- Keep the article body verbatim by default. Do not invent, summarize, translate, or rewrite technical claims. The only two standing exceptions are below, because LinkedIn cannot render them:
  - **Tables** become a readable bulleted list written as natural prose (Step 2b). The user wants it to read as if a person wrote it, never as a machine dump.
  - **Inline code** (`<code>` outside `<pre>`) becomes plain text wrapped in straight single quotes, for example `'last_activity_at'`. The LinkedIn editor has code blocks but no inline code mark.
- Keep code blocks inline. Do not ask whether to include them.
- Do not ask the user to confirm a title found in the RSS feed or canonical page.
- Pause only when authentication is required, the working tab is not in the foreground, source content is genuinely ambiguous after the recovery steps, or the irreversible Publish action needs confirmation.
- Never click Publish without explicit approval in the current chat. A previous approval is not reusable.
- Process one article per run.
- Report state precisely. Images or a cover "hydrated in the tab" are NOT "in the article". Say "listas para insertar, todavía no están en el artículo" until the figures exist in the editor DOM. Overstating progress here caused real confusion.
- When "la lista de CODERTECTURA", "la newsletter" or similar is mentioned, it means the CODERTECTURA LinkedIn newsletter. The draft inherits it from the author selector in the editor header (Step 7 verifies it).

## Prerequisites

1. Load the Chrome tools in one ToolSearch call: `tabs_context_mcp, navigate, computer, read_page, find, get_page_text, tabs_create_mcp, tabs_close_mcp, javascript_tool, browser_batch`.
2. Verify that the Claude in Chrome extension is connected.
3. Verify that LinkedIn is authenticated when first navigating there. If a login or challenge appears, pause and ask the user to complete it in the browser.

## Step 0 - Browser readiness (do this before any real input)

Real clicks, keystrokes, and screenshots only work when the working tab is the visible tab of a non-minimized Chrome window.

- Work in ONE tab for the whole run. Use the tab `tabs_context_mcp` gives you (create one only if the group is empty). Do NOT create a second tab to read the blog "on the side". A newly created tab becomes the active tab of the group and silently hides the LinkedIn tab. Navigate the same tab back and forth instead; the manifest in `localStorage` makes that cheap.
- Before the first real input, and again after any pause, check `document.visibilityState`:
  - When it is `hidden`, screenshots time out ("renderer may be frozen") and typed text is silently lost. ProseMirror never receives it, even though the tool reports success.
  - Clicks by `ref` may still focus fields, which makes the failure look intermittent.
- If the tab is hidden, stop and ask the user to bring the Chrome window with the "Edit article | LinkedIn" tab to the foreground. Do not press keys "to test" while hidden.
- `visibilityState` can lag right after the user brings the tab forward. A successful `screenshot` call is the reliable signal that input will land.
- If you did open an extra tab, close it with `tabs_close_mcp` as soon as you are done, then re-check visibility.

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
- Tables: `table` (any wrapper)
- Inline code: `code` not inside `pre`

Run `extractCodertecturaArticle()` from the scripts reference. It must return a manifest containing:

- Effective canonical URL, language, exact title, sanitized body HTML, and attribution HTML
- Cover URL
- Ordered media entries with stable IDs, absolute URLs, file names, captions, alt text, and marker text
- Ordered table entries with stable IDs, markers, headers, rows, and the lead-in sentence that precedes each table
- The ordered list of expected link hrefs (`expectedLinks`), used later to detect LinkedIn auto-links
- A source snapshot with the original body selector and structural counts before conversion
- Expected counts for headings, lists, blockquotes, code blocks, links, markers, media, and tables

NEVER return `bodyHtml`, `attributionHtml`, or any encoded payload as a tool result. Article HTML that contains tracking query strings is rejected by the output filter with `[BLOCKED: Cookie/query string data]`, and large payloads flood the context. Instead:

- Return only a summary: title, canonical URL and source, cover fields, `sourceSnapshot`, `expected`, `tables` (id, marker, headers, rows, leadIn), and a `media` array reduced to `id`, `marker`, `fileName`, `url`, `captionText`, `alt`.
- Persist the full manifest on the canonical origin with `localStorage.setItem('__liManifest', JSON.stringify(manifest))`. Every later trip back to the post reads it instead of re-running extraction, so the manifest stays byte-identical across trips and the long extraction script is sent once.
- Move `bodyHtml` to LinkedIn through the same hash channel used for images.

The extraction script applies these deterministic conversions:

- Replace every inline `code` (not inside `pre`) with its text wrapped in straight single quotes, BEFORE tables are processed, so table cells also get quoted identifiers. Never use typographic quotes.
- Replace every body image with a unique visible marker such as `[[LI_MEDIA_001]]`. Never locate an image by nearby prose.
- Replace every table with a unique marker paragraph such as `[[LI_TABLE_001]]` and record its cells in the manifest. Step 2b replaces the marker before anything reaches LinkedIn.
- Flatten galleries into consecutive image markers. Keep the gallery caption on the first image only.
- Convert `aside.notice` to `blockquote`, preserving its title, body, links, and position.
- Convert an iframe or video to a linked paragraph at the same position. If a local poster exists, insert the poster as an image before the link.
- Keep `p`, `h2`, `h3`, `strong`, `em`, `a`, `ul`, `ol`, `li`, `blockquote`, and `pre > code`.
- Convert relative `href` and media URLs with `new URL(value, canonicalUrl).href`.
- Remove navigation, metadata, sharing controls, comments, scripts, styles, SVG icons, lightbox wrappers (including the `<a>` that wraps a lightbox image), and presentation-only attributes.
- Use LinkedIn's native caption field only for link-free captions of at most 250 characters. If a caption contains one or more links, or exceeds 250 characters, leave the native caption empty and retain the complete rich caption as an emphasized paragraph immediately after the image.

ALWAYS append the following attribution paragraph at the end: *Publicado originalmente en [CODERTECTURA](canonical URL).*

- When `aside.notice--republished` exists, preserve that notice and use "Esta versión se publicó en CODERTECTURA" instead of claiming original publication.

Do not rewrite the opening or add a closing question unless the user explicitly requested adaptation. This conservative default removes an approval round trip and avoids changing the author's meaning.

### Generic interpretation rules

- Derive every structural count from the current live body. Never expect a fixed number of headings, paragraphs, lists, links, figures, or images.
- Treat zero counts as valid. An article may omit code, quotes, tables, notices, galleries, embeds, captions, or body images.
- Preserve the order of direct and nested body nodes as they appear in `.post__content`; do not infer order from filenames, numbering, visual position, or nearby text.
- Treat canonical and social metadata as optional. Use the final page URL and computed header background when those elements are absent.
- Treat a dedicated cover as optional. Reuse the first body image when no header or social cover exists; if the article has no images, do not invent a cover or block publication.
- Read image URLs from `src` and resolve them against the effective page URL. Lazy-loading state and an empty `currentSrc` do not mean that an image is missing.
- Treat classes such as `content-figure--lightbox` as presentation only. Extract the semantic image, alt text, caption, and caption links without carrying the lightbox wrapper into LinkedIn. The source link count therefore drops by one per lightbox anchor; that is expected.
- Preserve all caption links as clickable body links regardless of their domain, label, position, or number. Keep the complete caption around those links so their original context is not inferred or rewritten.
- Use each article's generated manifest as its own expected contract for the LinkedIn audit. Never compare one article with values captured from another article.

## Step 2b - Rewrite tables as a human-readable list

LinkedIn articles have no tables. Flattening rows into `Label | Column: value | Column: value` paragraphs is unreadable and looks machine-made. The user rejected that output. For each `[[LI_TABLE_nnn]]` in the manifest, write the replacement yourself:

- One bullet (`<li>`) per data row, in source order, inside one `<ul>`.
- Each bullet is one or two natural sentences in the article language that weave the row label and the column values together and contrast the columns. Example for a "Portal vs OpenTelemetry" table: "Los datos del portal viven en GitHub (dashboards, API, NDJSON) y es GitHub quien gobierna su ciclo de vida, con un máximo de 28 días. Con la telemetría OTel y 'capture.identity', acaban en tu colector OTLP y en tu backend de observabilidad, y el ciclo de vida lo gobiernas tú."
- Sound like the author: first or second person where the article does, vary how sentences open, and use connectors ("En latencia, …", "Para identificar a la persona, …", "Y, sobre todo, …" for the last row when it is the conclusion).
- Do NOT use these patterns: bold labels followed by a colon, "Columna: valor" prefixes, pipes, repeated identical sentence templates, or em-dash lists.
- Keep every fact, number, limit, and qualifier from every cell. Add nothing that the table does not say. Keep identifiers in single quotes (they already are, from the inline-code conversion).
- If the sentence right before the table refers to it ("Si tuviera que resumir la diferencia en una tabla, sería esta:"), rewrite only that sentence so it no longer mentions a table ("Si tuviera que resumir la diferencia, me quedaría con esto:").
- If a cell contained links, keep them as `<a href>` in the bullet; otherwise the expected link count drops.

Apply the rewrite on the canonical page with `applyTableRewrites()` from the scripts reference. It swaps each marker for your HTML, optionally replaces the lead-in sentence, updates `expected.lists`, and re-saves the manifest to `localStorage`. Show the rewritten list to the user in the final summary so they can review the wording.

## Step 3 - Run source preflight

Before touching LinkedIn, validate the manifest in one DOM call:

- Title and body are non-empty.
- The canonical URL is an HTTP or HTTPS URL.
- Cover URL and source are either both present or both absent. When present, the cover resolves to a valid image; when absent, the article contains no usable cover fallback.
- Every body image has a unique ID, marker, absolute URL, and file name.
- Marker count in `bodyHtml` equals media count.
- No `[[LI_TABLE_` marker and no inline `<code>` outside `<pre>` remains in `bodyHtml`.
- Every image URL is same-origin for CODERTECTURA and returns an image MIME type.
- Expected structural counts are recorded.
- The source snapshot identifies `.content.post__content` and its original direct-child, heading, list, link, figure, and image counts.
- No site chrome, comment heading, cookie text, or share links are present.
- Record `autolinkRisk`: tokens outside links that look like domains (`GitHub.com`, `user.name`, `host.name`, `process.user.name`, `example.io`). `.name`, `.io`, `.ai`, and `.dev` are real TLDs, so dotted identifiers are at risk. These do not fail preflight; they tell you what to check in Step 4b.

Retry extraction once after a page reload if preflight fails. If only the cover is missing, inspect the two metadata fallbacks once. Stop and explain the exact missing invariant rather than guessing a path.

## Step 4 - Draft the text once

1. Navigate to `https://www.linkedin.com/article/new/`. Fallback: `linkedin.com/feed/` → "Write article".
2. Confirm Step 0 (tab visible). Focus the Title field with `find` ("Title textarea") and a `left_click` on the returned `ref`, then type the title with the computer `type` action. Verify `textarea[placeholder="Title"]`'s value equals the manifest title before continuing. A coordinate click on the title can miss silently.
3. Capture the resulting editor URL (`/article/edit/<id>/`) after LinkedIn creates the draft and the indicator reads "Draft - saved". Reuse this exact URL for every hash transfer.
4. Return to the canonical post (same tab) and build ONE `CLAUDEBUNDLE=` payload with `prepareBundle()`. It packs `bodyHtml`, every body image, and the cover, in that order and while they fit under 1.2 MB. A typical article with three images and a 2.8 MB PNG cover fits in about 1.13 MB after recompression, so the whole draft usually needs a single trip. Send it with `navigateBundle(editorUrl)`.
5. Wait outside the browser tool (about 8 s), then make `hydrateBundleAndPaste()` the first JavaScript call. It hydrates `window.__files`, stores the lite manifest that travels in the bundle as `window.__liManifest` (and in `sessionStorage`, so it survives the Step 6 reload), strips the hash with `history.replaceState`, and pastes the HTML into `div.ProseMirror[contenteditable="true"]` in that single call. Every LinkedIn-side audit uses that lite manifest.
6. The HTML starts with `<p></p>` so ProseMirror's first-block merge is absorbed.
7. Run `auditLinkedInDraft(manifest)` immediately.

The editor does not understand Markdown text. Paste HTML only. LinkedIn may normalize both `h2` and `h3` to `h3.article-editor-heading`, so compare total heading count rather than heading levels.

The `<p></p>` prefix is usually NOT absorbed and survives as a leading empty paragraph. Remove it with real input, not DOM selection:

1. Read the rect of the first text block (`children[1]`) WITHOUT scrolling (the page is at the top after the paste) and convert it to screenshot coordinates.
2. Click a few pixels in from its left edge on its first line.
3. ASSERT that `document.activeElement` is the editor (`aria-label="Article editor content"`) BEFORE pressing any key. In this run a click meant for the body landed in the title, and the following `BackSpace` deleted a space from the title ("atribución detelemetría"). Never press `BackSpace`, `Delete`, or type unless focus is verified.
4. Press `Home`, then `BackSpace`.
5. Verify that the block count dropped by one, that the title is unchanged, and that heading, link, and code-block counts are unchanged.

Setting a DOM range on the empty paragraph and pressing `Delete` does nothing. `ctrl+Home` from a click in the body is also unreliable. Clicking slightly too high lands in the empty paragraph itself, where `BackSpace` is a no-op. If the block count does not change, re-measure and click lower, on actual text.

If the title was damaged, fix it with real input: click the title, `ctrl+a` (selects only the textarea), and retype the exact manifest title.

Never clear and repaste a non-empty draft unless the user explicitly asks to start over. When they do, reuse the same draft rather than creating a second one: click into the body, `ctrl+a`, `BackSpace`, and confirm the editor reports one empty block and zero figures. The title survives. Never delete or discard the draft itself — that is the user's call, not yours.

## Step 4b - Remove LinkedIn auto-links

On paste (and only on paste; typed text was not observed to auto-link), LinkedIn turns domain-looking tokens into links. In this run that hit `user.name`, `process.user.name`, `host.name`, and `GitHub.com`. Run `findUnexpectedLinks(manifest)`: every anchor whose href is not in `manifest.expectedLinks` is an auto-link. Remove each one with real input:

1. Read the link's rect and convert it to screenshot coordinates.
2. `double_click` the link. Assert that `getSelection().toString()` equals the full link text. For multi-dot tokens, the double-click selects the whole token.
3. `type` the exact same text. The replacement text does not inherit the link mark, so the link disappears and the text is unchanged.
4. Re-run `findUnexpectedLinks()`.

Do NOT use the toolbar Link button: it opens an "Edit link" dialog with only Cancel and Apply. Do not rely on the hover popover's trash icon either; it removes the link when it appears, but it appears inconsistently.

## Step 5 - Transfer and place images

LinkedIn's CSP blocks external image fetches and remote images in pasted HTML. Use the hash-transfer functions from the scripts reference in the same tab.

Skip steps 1 to 6 for images already hydrated by the Step 4 bundle; go straight to placement. `window.__files` survives until the next navigation or reload of the editor. If the user reloads, or the tab is navigated, re-hydrate before placing.

1. Wait until the draft reports saved before leaving LinkedIn.
2. Navigate the same tab to the canonical CODERTECTURA URL and read the manifest from `localStorage`.
3. Fetch the cover and body images from their absolute manifest URLs.
4. Normalize the remaining images with `prepareNextImagePayload()`. Keep small files unchanged; resize and recompress large raster images to stay within the hash budget. Preserve a small GIF; convert an oversized GIF to a static JPEG preview.
5. Let the function fill one encoded payload below 1.2 MB and return `includedNames` plus `remainingNames`. Do not estimate batches manually.
6. Navigate to the exact saved editor URL with the prepared hash. The first JavaScript call after navigation MUST be `hydrateTransferredImageFiles()` so it hydrates `window.__files` and strips the hash with `history.replaceState` in that same call. Do not run another browser, DOM, or JavaScript action first because tool responses can echo the complete base64 URL and overflow the tab context.
7. Place each included body image with a real selection, one at a time and in manifest order:
   1. Use `find` with the query "paragraph containing exactly the text [[LI_MEDIA_nnn]]", then `computer scroll_to` that `ref`, wait about 2 s, and read the marker block's rect with `locateMarkerBlockNoScroll(marker)`. LinkedIn keeps adjusting the scroll position for a moment after any `scrollIntoView`. Coordinates read in the same call as a JS scroll can be stale by hundreds of pixels.
   2. `triple_click` those coordinates with the computer tool. This selects the whole marker paragraph AND syncs ProseMirror's internal selection. A `triple_click` by `ref` worked twice and then selected the previous list item, so prefer coordinates.
   3. In one JavaScript call, assert `window.getSelection().toString().trim() === marker` and THEN dispatch the file paste. Throw instead of pasting if the assertion fails. This assertion caught a wrong selection in practice; nothing was pasted and the retry succeeded.
   4. Wait outside the browser tool (about 12 s), then verify.
8. After each image, verify that the figure count increased by exactly one, that the figure sits between the expected neighbours, and that the marker is gone. Two new figures, or a figure adjacent to the previous one instead of at the marker, means the selection was wrong. Stop and report rather than continuing, because every later insertion compounds the damage.
9. Type each caption with real keystrokes:
   1. Use `find` ("empty image caption textarea under the Nth image") and `left_click` the returned `ref`. Coordinate clicks on captions missed because of scroll drift.
   2. Assert that `document.activeElement` is the Nth `figure figcaption textarea` in the editor.
   3. `type` the caption.

   Captions written through the native `value` setter look correct in the DOM and are silently discarded on save.
10. If `remainingNames` is non-empty, return to the canonical post, read the manifest from `localStorage`, and prepare only those remaining media. Repeat until none remain.
11. If the manifest has a cover URL, upload it last:
    1. Run `openArticleCoverCrop(fileName)` and verify the `crop-ready` state.
    2. Run `confirmArticleCoverCrop()` as a separate action and require the `applied` state.
    3. A timeout waiting for the final cover image is indeterminate: inspect `getArticleCoverUploadState()` before retrying. If the crop dialog remains open, click its enabled Next button once; if the cover is already applied, continue without uploading again.
    4. Restore every patched browser prototype in a `finally` path.

    If the manifest has no cover URL, skip cover upload.

Marker-based placement is mandatory. It works for images at the beginning, adjacent figures, repeated prose, and galleries, all of which make nearby-text anchoring unreliable.

## Step 6 - Final audit and recovery

Wait for "Draft - saved", reload the editor URL once, and then run one manifest-aware DOM audit (`auditLinkedInDraft(manifest, { requireMedia: true, requireSaved: true })`). Require all of the following:

- Exact title
- Expected total headings, lists, blockquotes, and code blocks
- Expected link count, counted as link RUNS. After a reload LinkedIn splits one link into several adjacent `<a>` elements around an `<em>` ("referencia de *enterprise managed settings*" became two anchors with the same href). Adjacent anchors with the same href and no text between them count as one. The audit script does this.
- No unexpected links (auto-links) — every href is in `manifest.expectedLinks`
- Figure count equal to body media count
- Captions equal to their planned plain text
- No `[[LI_MEDIA_` or `[[LI_TABLE_` markers, no ` | ` table residue
- Inline-code identifiers present in straight single quotes, and no typographic quotes (`‘` `’`) introduced
- Final attribution present and linked to the canonical URL
- Cover presence matches the manifest: present when a dedicated or fallback cover was resolved, absent otherwise
- No empty top-level paragraphs, EXCEPT the one LinkedIn inserts immediately after each figure and the trailing editor placeholder
- Draft saved indicator present

Count only top-level editor blocks and `li` elements directly. In LinkedIn's list markup each `li` wraps a `p`, so a selector like `p, li` counts every list item twice.

LinkedIn adds an empty paragraph after every inserted image. LEAVE IT. It is invisible spacing in the published article, and removing it is actively harmful: placing the caret at the start of the following heading and pressing `BackSpace` demotes that heading to a paragraph instead of deleting the empty block. If this happens, `ctrl+z` restores the heading — verify the heading count returns to expected before continuing. Expect a final block count of `body blocks + one per figure`.

Inserted images stay as local `data:` URLs in the DOM until a reload, which is NOT evidence of a failed upload; after the reload they resolve to `media.licdn.com`. A figure whose `src` attribute is the literal string `null`, or whose `naturalWidth` is 0, IS a failed insertion.

Repair only the failed element. Re-query the live DOM before one retry. Do not repeat successful uploads, repaste the body, or restart the article. If the second attempt fails, stop with the failed invariant, expected value, and observed value.

Take one screenshot at the top only after the DOM audit passes.

## Step 7 - Prepare the publish dialog

1. Check the editor header: the author selector shows the publication target. For CODERTECTURA it reads "Rodrigo … / CODERTECTURA", meaning the article is a newsletter edition. Leave it as is unless the user asks otherwise.
2. Click "Next" in the editor header. LinkedIn shows the share/publish step: a post composer where the article will be attached. For a newsletter edition the placeholder reads "Tell your network what this edition of your newsletter is about…" and the audience reads "Post to Anyone + Subscribers". Confirm both.
3. Click the composer and fill it with a warm teaser in the article language: two to four conversational, friendly, first-person sentences stating the hook and what the reader will get. Base it only on claims the article makes.
4. Press `Return` twice, then type three to five short, common hashtags on that separate line, ending with a space so the hashtag suggestion popup closes. Prefer tags already represented by the article title, categories, or tags. Avoid long compound hashtags. Never press `Escape` in the dialog: it can close the composer.
5. ALWAYS add the `#MVPBuzz` hashtag.
6. Show the exact teaser and hashtags in chat and state that the dialog is ready.
7. Stop before Publish and request explicit confirmation. If the user says "publish" in the current chat, click Publish once and verify the published confirmation or resulting article URL.

Closing the dialog (X) keeps the draft but DISCARDS the teaser. After any further edit to the article, reopen the dialog with "Next" and retype the same teaser and hashtags. If the user asked for edits to the teaser, edit in the dialog rather than starting over.

## Step 8 - Post-review edits to the draft

The user often reviews the draft and asks for changes before publishing. Close the publish dialog first (the draft is kept), then edit in place. Never repaste the whole body. Two techniques are proven reliable:

- **Replace a span of text inside one block** (quoting an identifier, fixing a word):
  1. Select it with `selectTextInEditor(before, term, after)`. It builds a DOM range, dispatches `selectionchange`, waits 600 ms, and asserts that the selected text equals the term.
  2. `type` the replacement with real keystrokes. Surrounding bold and italic are preserved, and typed text is not auto-linked.
  3. Verify with `checkTextInEditor(before + replacement + after)`.

  Twenty consecutive replacements succeeded this way.
- **Replace whole blocks** (rewriting a section, swapping a flattened table for a list): select from the first text node of the first block to the end of the last block with the same range + `selectionchange` + wait + assert pattern, then dispatch an HTML paste. Then run Step 4b, because pasted text can be auto-linked.

Rules for both:

- Build each match from its context (`before + term + after`) and require exactly one match. Common words such as "prompts" or "identity" also appear in normal prose, and only the occurrence that was code in the source may change.
- When several edits fall in the same block, apply them from last to first so the `before` context of the remaining ones stays valid.
- After edits, wait for "Draft - saved", reload, rerun the Step 6 audit, then redo Step 7.

## Speed and stability rules

- Prefer DOM checks over screenshots, but use a screenshot to confirm the tab is really visible before real input.
- Compute click coordinates from live rects, never from a screenshot by eye. The screenshot frame is scaled against CSS pixels: derive `k = screenshotWidth / window.innerWidth` once (0.6125 on a 2560 px viewport, frame 1568 px) and convert with `Math.round(cssX * k)`.
- LinkedIn's editor page keeps adjusting the scroll position for a moment after `scrollIntoView`, after focus changes, and after uploads. Either read the rect after a ~2 s wait without scrolling again, or use `find` + `ref` actions (`left_click` / `scroll_to`). Re-read coordinates immediately before every click.
- Verify the effect of every click before pressing keys: check `document.activeElement` (editor, title textarea, or the specific caption textarea).
- Do not trust a collapsed `window.getSelection()` read after a click; it can report the previously focused block. A non-collapsed selection (after `triple_click` or `double_click`) reads reliably, so verify by selected TEXT rather than by anchor node.
- A synthetic DOM range alone does not drive ProseMirror: pressing `Delete` on it does nothing. The same range IS honoured after `document.dispatchEvent(new Event('selectionchange'))` plus a ~600 ms wait. Real keystrokes or a dispatched paste then act on it reliably. Always assert the selected text first.
- The tool output filter blocks some dotted identifiers (for example `process.user.name`, `telemetry.capture.identity`, `enduser.pseudo.id`) as `[BLOCKED: JWT token]`, and blocks hostnames inside URLs the same way. Do comparisons inside JavaScript and return booleans or counts, or replace `.` with `·` in returned strings.
- Use the canonical page DOM, never RSS `description`, as article content.
- Carry one manifest through extraction, table rewrite, paste, upload, and final audit.
- Batch read-only checks; keep image uploads sequential because each changes editor state.
- Allow at most one targeted retry per failed action.
- Batch predictable steps with browser_batch. A batch cannot act on a page after a `navigate` inside it. Issue `navigate` alone, then batch the actions on the loaded page.
- After hash navigation, wait outside the browser tool so tool output does not echo the large URL.
- Make the hydrate function the first JavaScript call after every hash navigation. Do not inspect the tab or editor before that call removes the payload URL.
- Treat a browser or CDP timeout during an upload as unknown completion state. Inspect the live DOM and recover placement before deciding whether a retry is safe.
- Treat cover selection, crop readiness, and final application as separate states. Never infer that the upload failed only because the final cover selector timed out.
- Do not use `window.open`, `target=_blank`, or popups to bridge tabs. Do not open a second tab in the group (see Step 0).
- Do not close the working tab mid-flow.
- Remote `<img src>` in pasted HTML is rejected by the editor schema; data transfer is genuinely required.
- Never use `fetch()` from the LinkedIn tab for external URLs or data URLs; its CSP blocks both.
- Restore patched browser APIs even when the cover upload fails.
- Do not publish more than one assisted article per run.
