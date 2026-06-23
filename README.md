# CODERTECTURA Blog

Static blog powered by Hugo.

## Local build

The repository uses the in-repo Hugo executable at `.tools/hugo/hugo.exe` for local validation on Windows:

- Build preview output: `./.tools/hugo/hugo.exe --gc --minify --destination public-hugo-preview`
- Generated output is ignored by Git (`public/`, `public-hugo-preview/`, `resources/`, `.hugo_build.lock`).

## Deployment

Azure Static Web Apps builds Hugo in GitHub Actions and uploads the generated `public/` directory with app build skipped.

## Reusable content components (Hugo shortcodes)

Repeated content patterns are implemented as Hugo shortcodes in [`layouts/shortcodes/`](layouts/shortcodes) so posts stay consistent and free of copy-pasted raw HTML. Author posts with these shortcodes instead of hand-written `<div>`/`<figure>`/`<iframe>` markup.

| Shortcode | Purpose |
| --- | --- |
| `notice` | Coloured callout / admonition box (info, warning, success, danger, …). |
| `republished` | Cross-post attribution banner ("Artículo publicado originalmente en…"). |
| `callout` | Same as `notice` but adds the extra `callout` class for emphasis. |
| `figure` | Single image with optional caption, alignment, border and lightbox. |
| `gallery` | Responsive grid of images with optional lightbox. |
| `video` | Self-hosted `<video>` (mp4/webm/ogg) or embedded player, responsive. |
| `responsive-embed` | Generic responsive `<iframe>` wrapper for embedded content. |

### `notice`

Renders an accessible `<aside class="notice notice--TYPE" role="note">` box. The body is written as normal Markdown between the tags (lists, links and emphasis are all rendered).

Parameters:

- `type` (or first positional arg) — `info` (default), `warning`, `success`, `danger`, `note`, `primary`.
- `title` (or `caption`) — optional bold heading.
- `class` — extra CSS classes.

```text
{{< notice type="warning" >}}
*Este es un artículo «legacy»* que mantengo como recuerdo de mi recorrido técnico.
{{< /notice >}}

{{< notice type="info" title="Serie" >}}
- [Parte 1: Implementación](/posts/aop-parte-1)
- [Parte 2: Logging](/posts/aop-parte-2)
{{< /notice >}}
```

### `republished`

Renders the standard cross-post attribution banner (an `info` notice) for posts first published on another blog. It centralises the exact wording and links, so the boilerplate only ever lives in one place.

Parameters:

- `url` (required) — URL of the original publication.
- `blog` (required) — display name of the origin blog (guillemets `« »` are added automatically).
- `publisher` — publisher name. Default: `ENCAMINA`.
- `publisherURL` — publisher URL. Default: `https://www.encamina.com/`.
- `type` — notice colour variant. Default: `info`.

```text
{{< republished blog="Piensa en software, desarrolla en colores" url="https://blogs.encamina.com/piensa-en-software-desarrolla-en-colores/integrando-otros-llms-con-semantic-kernel/" >}}
```

Renders as: *Artículo publicado originalmente en el blog «Piensa en software, desarrolla en colores» de ENCAMINA.*

### `callout`

Identical API to `notice` (same `type`, `title`, `class` parameters) but adds the `callout` class for a slightly stronger visual treatment.

### `figure`

Single image with optional caption and lightbox.

Parameters: `src` (or `imagePath`/`path`/`image`), `caption`, `alt` (defaults to the caption or page title), `class` (e.g. `align-center`, `align-left`, `align-right`), `imageClass`, `imageStyle`, `imageBorder`, `lightbox` (default `true`).

```text
{{< figure src="/images/post/diagram.png" caption="Arquitectura de la solución" class="align-center" >}}{{< /figure >}}
```

### `gallery`

Responsive grid of images.

Parameters: `images` (or `src`, comma-separated paths), `id` (front-matter key holding image items), `caption`, `alt`, `class`, `lightbox` (default `true`).

```text
{{< gallery images="/images/post/1.png, /images/post/2.png, /images/post/3.png" caption="Galería del evento" >}}{{< /gallery >}}
```

### `video`

Responsive video. A `.mp4`/`.webm`/`.ogg` `src` renders a native `<video>`; any other `src` renders an embedded `<iframe>`.

Parameters: `src` (or `url`), `poster`, `title` (or `caption`), `caption`, `class`, `ratio` (default `16 / 9`), `referrerpolicy`.

```text
{{< video src="https://www.youtube.com/embed/VIDEO_ID" title="Charla" >}}
```

### `responsive-embed`

Generic responsive `<iframe>` wrapper for arbitrary embedded content.

Parameters: `src` (or `url`), `title` (or `caption`), `ratio` (default `16 / 9`), `allow`, `referrerpolicy`, `style`, `class`. With no `src`, the inner content is emitted inside the responsive wrapper.

```text
{{< responsive-embed src="https://example.com/embed" title="Demo embebida" ratio="4 / 3" >}}
```

### Notes for maintainers

- All notice variants (`notice`, `callout`, `republished`) share the same box styling in [`assets/css/main.css`](assets/css/main.css); the `type` only changes the accent colour. Avoid per-post inline `style` attributes — adjust the component or its CSS instead.
- External links in post bodies still use raw `<a href="…" target="_blank" rel="noopener noreferrer">` markup. This is a candidate for a future link [render hook](https://gohugo.io/render-hooks/links/) so the `target`/`rel` boilerplate can be removed from the Markdown.
