#!/usr/bin/env python3
"""Resolve body-image placeholders in a generated CODERTECTURA post (Phase 2).

``generate_article.py`` may leave ``{{img:<id>}}`` placeholders in a draft and
write a companion spec file (``BODY_IMAGES_FILE``) describing each one. This script
turns those placeholders into real ``{{< figure >}}`` shortcodes:

* ``type: "ai"`` placeholders are rendered with the MAI image model (shared with
  ``generate_image.py`` via :class:`FoundryImageClient`) and saved to
  ``static/images/<slug>/body-<n>.png``.
* ``type: "source"`` placeholders extract a REAL image from an allowlisted source
  article. The download is defended in depth: the URL host must be on the official
  Microsoft/GitHub allowlist, redirects to off-allowlist hosts are blocked, the
  FINAL URL host is re-validated (SSRF/exfiltration defence), and the bytes are
  validated by magic number AND a size cap BEFORE anything is written. The figure
  caption carries a visible attribution link back to the source article.

Resilience model
----------------
* **Fail-open per image**: if one image fails (generation error, blocked download,
  bad bytes), it is logged with ``warn`` and its placeholder is simply removed, so
  the article stays clean. The cover image (``generate_image.py``) remains the
  hard-required one; body images are best-effort enrichment.
* **Fail-safe overall**: an absent/empty spec is a no-op success. Genuine
  misconfiguration (a non-empty spec with no resolvable post) is a hard error.

Inputs (environment variables only)
------------------------------------
BODY_IMAGES_FILE       Path to the JSON spec written by generate_article.py:
                       ``{slug, post_path, images:[...]}``. Absent/empty -> no-op.
POST_PATH              The .md file to rewrite. Falls back to the spec's
                       ``post_path``.
POST_SLUG              Slug used to derive ``static/images/<slug>/``. Falls back to
                       the spec's ``slug``.
STATIC_IMAGES_DIR      Image root. Default: static/images.
AOAI_ENDPOINT          Foundry endpoint (required only when AI body images exist).
AOAI_IMAGE_DEPLOYMENT  Image deployment, e.g. MAI-Image-2.5 (AI body images only).
AOAI_TOKEN             Pre-acquired bearer token, env ONLY (AI body images only).
AOAI_BODY_IMAGE_SIZE   AI body-image size. Default: 1024x1024.
AOAI_IMAGE_TIMEOUT     Image-generation HTTP timeout (seconds). Default: 300.
BODY_IMAGE_DOWNLOAD_TIMEOUT   Source-image download timeout (seconds). Default: 30.
BODY_IMAGE_MAX_BYTES   Max accepted source-image size in bytes. Default: 8388608.

Output
------
* Rewrites POST_PATH in place (UTF-8, ``\\n``), swapping resolved placeholders for
  figure shortcodes and removing any unresolved ones.
* Writes the produced images under ``static/images/<slug>/``.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from _foundry import USER_AGENT, FoundryError, FoundryImageClient, fail, warn
from _sources import (
    extract_host,
    host_is_allowed,
    is_denylisted_image,
    is_http_url,
    sanitize_untrusted_text,
)

# Style wrapper for AI body illustrations/diagrams. This is INTENTIONALLY the calm,
# explanatory counterpart to the cover STYLE_SUFFIX in generate_image.py: the cover
# is now dramatic/cinematic with a hero subject, while body images stay flat, clean
# and didactic for inline concepts/diagrams. Do NOT "re-sync" this with the cover
# suffix -- the divergence is deliberate. Same CODERTECTURA palette: deep midnight
# navy-to-black background, luminous teal/cyan with neon-green accents, soft glow,
# clean geometric shapes and subtle grid lines. Always label/logo-free.
BODY_STYLE_SUFFIX = (
    " -- clean modern conceptual technical illustration or diagram, flat explanatory "
    "style, deep midnight navy-to-black background with luminous teal, cyan and "
    "neon-green accents, soft glow, geometric shapes and subtle grid lines, "
    "no text, no letters, no numbers, no labels, no logos, no brands, no watermarks."
)

# Default hard cap on a downloaded source image (8 MiB). Bytes are checked against
# this BEFORE being written to disk.
DEFAULT_MAX_IMAGE_BYTES = 8 * 1024 * 1024

# Body-image placeholder convention, mirrored from generate_article.py:
# {{img:<id>}} with id in [A-Za-z0-9_-].
_PLACEHOLDER_RE = re.compile(r"\{\{img:([A-Za-z0-9_-]+)\}\}")


# -----------------------------------------------------------------------------
# Image-byte validation (magic number + size cap). Treats all bytes as UNTRUSTED.
# -----------------------------------------------------------------------------


def detect_image_type(data: object) -> "str | None":
    """Return ``png|jpg|webp|gif`` from the leading magic bytes, or None.

    PNG : ``89 50 4E 47 0D 0A 1A 0A``; JPEG: ``FF D8 FF``; WebP: ``RIFF....WEBP``;
    GIF : ``GIF87a`` / ``GIF89a``. Anything else is rejected.
    """
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12:
        return None
    head = bytes(data[:12])
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return None


def validate_image_bytes(data: bytes, *, max_bytes: int) -> str:
    """Return the validated extension, or raise :class:`FoundryError`."""
    if len(data) > max_bytes:
        raise FoundryError(f"image exceeds the {max_bytes}-byte size cap")
    ext = detect_image_type(data)
    if ext is None:
        raise FoundryError(
            "downloaded bytes are not a recognised image (PNG/JPEG/WebP/GIF)"
        )
    return ext


# -----------------------------------------------------------------------------
# Allowlisted, redirect-safe image download (SSRF / exfiltration defence).
# -----------------------------------------------------------------------------


class _AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that refuses to follow redirects off the allowlist."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        if not (is_http_url(newurl) and host_is_allowed(newurl)):
            raise FoundryError(
                f"blocked redirect to non-allowlisted location: {extract_host(newurl)!r}"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _build_allowlist_opener() -> urllib.request.OpenerDirector:
    """Build an opener that re-validates every redirect target against the allowlist."""
    return urllib.request.build_opener(_AllowlistRedirectHandler)


def download_allowlisted_image(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    opener: "urllib.request.OpenerDirector | None" = None,
) -> "tuple[bytes, str]":
    """Download ``url`` (allowlisted only) and return ``(bytes, ext)``.

    Raises :class:`FoundryError` if the URL is not an allowlisted ``http(s)`` URL,
    a redirect leaves the allowlist, the final URL host is off-allowlist, the size
    cap is exceeded, or the bytes are not a recognised image. Nothing is written
    here — the caller persists the validated bytes.
    """
    if not is_http_url(url) or not host_is_allowed(url):
        raise FoundryError(
            f"refusing to download non-allowlisted image URL (host {extract_host(url)!r})"
        )
    if is_denylisted_image(url):
        raise FoundryError(
            f"refusing denylisted source image URL (host {extract_host(url)!r})"
        )
    opener = opener or _build_allowlist_opener()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            if not host_is_allowed(final_url):
                raise FoundryError(
                    f"final image URL host not allowlisted: {extract_host(final_url)!r}"
                )
            if is_denylisted_image(final_url):
                raise FoundryError(
                    f"final image URL is denylisted (host {extract_host(final_url)!r})"
                )
            # Loop-read up to one byte beyond the cap, accumulating across short
            # reads so a fragmented socket can never slip an over-cap payload under
            # the limit. We never hold more than ``max_bytes + 1`` bytes, which is
            # exactly enough for the cap check below to fire.
            limit = max_bytes + 1
            chunks: "list[bytes]" = []
            received = 0
            while received < limit:
                chunk = response.read(limit - received)
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
            data = b"".join(chunks)
    except FoundryError:
        raise
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise FoundryError(
            f"could not download image from {extract_host(url)!r}: {exc}"
        ) from exc

    if not isinstance(data, (bytes, bytearray)):
        raise FoundryError("image download returned no bytes")
    payload = bytes(data)
    ext = validate_image_bytes(payload, max_bytes=max_bytes)
    return payload, ext


# -----------------------------------------------------------------------------
# Shortcode rendering (never inject raw model text into shortcode params).
# -----------------------------------------------------------------------------


def shortcode_safe(text: object, *, max_length: int = 400) -> str:
    """Sanitise text for use inside a double-quoted Hugo shortcode parameter."""
    cleaned = sanitize_untrusted_text(text, max_length=max_length)
    for char in ('"', "`", "<", ">", "{", "}"):
        cleaned = cleaned.replace(char, "")
    return cleaned.strip()


def _safe_link_url(url: object) -> str:
    """Sanitise an (already allowlisted) URL for a Markdown link destination."""
    cleaned = sanitize_untrusted_text(url, max_length=400)
    for char in (" ", '"', "'", "`", "(", ")", "<", ">", "{", "}", "\\"):
        cleaned = cleaned.replace(char, "")
    return cleaned


def figure_shortcode(*, src: str, alt: str, caption: str) -> str:
    """Build a ``{{< figure >}}`` call with safely-quoted parameters."""
    parts = [f'src="{src}"']
    if alt:
        parts.append(f'alt="{alt}"')
    if caption:
        parts.append(f'caption="{caption}"')
    return "{{< figure " + " ".join(parts) + " >}}"


def normalise_placeholder(value: object) -> "str | None":
    """Return a canonical ``{{img:<id>}}`` token, or None if unusable."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    match = re.fullmatch(r"\{\{\s*img\s*:\s*([A-Za-z0-9_-]+)\s*\}\}", text)
    if match:
        return "{{img:" + match.group(1) + "}}"
    if re.fullmatch(r"[A-Za-z0-9_-]+", text):
        return "{{img:" + text + "}}"
    return None


# -----------------------------------------------------------------------------
# Per-image resolution + Markdown rewrite.
# -----------------------------------------------------------------------------


def _write_bytes(path: str, data: bytes) -> None:
    """Write ``data`` to ``path``, creating parent directories as needed."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def resolve_image(
    item: dict,
    n: int,
    *,
    slug: str,
    images_dir: str,
    image_client: "FoundryImageClient | None",
    downloader,
    size: str,
    max_bytes: int,
    download_timeout: float,
) -> "str | None":
    """Resolve one body-image spec to a figure shortcode, or None on failure.

    Returns the shortcode string when the image is produced and saved; returns
    ``None`` (fail-open) when anything goes wrong, so the caller removes the
    placeholder and leaves a clean article.
    """
    placeholder = normalise_placeholder(item.get("placeholder")) or "{{img:?}}"
    kind = item.get("type")
    alt = shortcode_safe(item.get("alt"), max_length=200)
    caption_text = shortcode_safe(item.get("caption"), max_length=300)

    if kind == "ai":
        prompt = (item.get("prompt_en") or "")
        prompt = prompt.strip() if isinstance(prompt, str) else ""
        if not prompt:
            warn(f"{placeholder}: AI body image has no prompt; removing placeholder")
            return None
        if image_client is None:
            warn(f"{placeholder}: no image client available; removing AI placeholder")
            return None
        try:
            data = image_client.generate(prompt + BODY_STYLE_SUFFIX, size=size)
        except FoundryError as exc:
            warn(f"{placeholder}: AI image generation failed ({exc}); removing placeholder")
            return None
        if not data or len(data) < 100:
            warn(f"{placeholder}: AI image was unexpectedly small; removing placeholder")
            return None
        filename = f"body-{n}.png"
        _write_bytes(os.path.join(images_dir, filename), data)
        return figure_shortcode(
            src=f"/images/{slug}/{filename}", alt=alt, caption=caption_text
        )

    if kind == "source":
        image_url = item.get("image_url")
        source_url = item.get("source_url")
        if not isinstance(image_url, str) or not host_is_allowed(image_url):
            warn(f"{placeholder}: image_url missing/not allowlisted; removing placeholder")
            return None
        if not isinstance(source_url, str) or not host_is_allowed(source_url):
            warn(f"{placeholder}: source_url missing/not allowlisted; removing placeholder")
            return None
        try:
            data, ext = downloader(image_url, timeout=download_timeout, max_bytes=max_bytes)
        except FoundryError as exc:
            warn(
                f"{placeholder}: source image download/validation failed ({exc}); "
                "removing placeholder"
            )
            return None
        filename = f"source-{n}.{ext}"
        _write_bytes(os.path.join(images_dir, filename), data)
        host = extract_host(source_url)
        attribution = f"Fuente: [{host}]({_safe_link_url(source_url)})"
        caption = f"{caption_text} {attribution}".strip() if caption_text else attribution
        return figure_shortcode(
            src=f"/images/{slug}/{filename}", alt=alt, caption=caption
        )

    warn(f"{placeholder}: unknown body image type {kind!r}; removing placeholder")
    return None


def rewrite_markdown(text: str, replacements: dict) -> str:
    """Swap each resolved placeholder for its shortcode; strip any leftovers.

    ``replacements`` maps a canonical ``{{img:<id>}}`` token to its figure
    shortcode. Tokens not present in the map (failed or orphaned) are removed, so
    a published article never ships a raw placeholder.
    """
    for placeholder, shortcode in replacements.items():
        text = text.replace(placeholder, shortcode)
    # Remove any remaining {{img:...}} tokens (failures / orphans).
    text = _PLACEHOLDER_RE.sub("", text)
    # Tidy: blank out whitespace-only lines and collapse 3+ newlines to one blank.
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def spec_images(spec: dict) -> list:
    """Return the list of image-spec dicts from a spec mapping (``images`` key)."""
    images = spec.get("images")
    if not isinstance(images, list):
        images = spec.get("body_images")
    if not isinstance(images, list):
        return []
    return [item for item in images if isinstance(item, dict)]


def process(
    spec: dict,
    *,
    post_path: str,
    slug: str,
    static_images_dir: str,
    image_client: "FoundryImageClient | None",
    downloader,
    size: str,
    max_bytes: int,
    download_timeout: float,
) -> int:
    """Resolve every image in ``spec`` and rewrite ``post_path``. Returns the count."""
    images = spec_images(spec)
    with open(post_path, "r", encoding="utf-8") as handle:
        text = handle.read()

    images_dir = os.path.join(static_images_dir, slug)
    replacements: dict = {}
    for index, item in enumerate(images, start=1):
        placeholder = normalise_placeholder(item.get("placeholder"))
        shortcode = resolve_image(
            item,
            index,
            slug=slug,
            images_dir=images_dir,
            image_client=image_client,
            downloader=downloader,
            size=size,
            max_bytes=max_bytes,
            download_timeout=download_timeout,
        )
        if placeholder and shortcode:
            replacements[placeholder] = shortcode

    new_text = rewrite_markdown(text, replacements)
    if new_text != text:
        with open(post_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(new_text)
    return len(replacements)


# -----------------------------------------------------------------------------
# Spec loading + CLI plumbing.
# -----------------------------------------------------------------------------


def load_spec(path: str) -> "dict | None":
    """Read + parse the BODY_IMAGES_FILE spec, or None for a no-op."""
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        warn(f"could not read BODY_IMAGES_FILE ({path}): {exc}")
        return None
    if not text.strip():
        return None
    try:
        spec = json.loads(text)
    except json.JSONDecodeError:
        warn("BODY_IMAGES_FILE did not contain valid JSON")
        return None
    return spec if isinstance(spec, dict) else None


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        fail(f"{name} must be a number (seconds)")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        fail(f"{name} must be an integer")


def main() -> None:
    spec = load_spec(os.environ.get("BODY_IMAGES_FILE", "").strip())
    if spec is None:
        print("No body-image spec to resolve; nothing to do.")
        return

    images = spec_images(spec)
    if not images:
        print("Body-image spec is empty; nothing to do.")
        return

    post_path = os.environ.get("POST_PATH", "").strip()
    if not post_path:
        candidate = spec.get("post_path")
        post_path = candidate.strip() if isinstance(candidate, str) else ""
    if not post_path:
        fail("body-image spec has images but no POST_PATH (or spec.post_path) was provided")
    if not os.path.isfile(post_path):
        fail(f"post file not found: {post_path}")

    slug = os.environ.get("POST_SLUG", "").strip()
    if not slug:
        candidate = spec.get("slug")
        slug = candidate.strip() if isinstance(candidate, str) else ""
    if not slug:
        fail("no slug available (set POST_SLUG or include 'slug' in BODY_IMAGES_FILE)")

    static_images_dir = (
        os.environ.get("STATIC_IMAGES_DIR", "static/images").strip() or "static/images"
    )
    size = os.environ.get("AOAI_BODY_IMAGE_SIZE", "1024x1024").strip() or "1024x1024"
    image_timeout = _float_env("AOAI_IMAGE_TIMEOUT", 300.0)
    download_timeout = _float_env("BODY_IMAGE_DOWNLOAD_TIMEOUT", 30.0)
    max_bytes = _int_env("BODY_IMAGE_MAX_BYTES", DEFAULT_MAX_IMAGE_BYTES)

    # An image client is only needed when at least one AI body image is present.
    image_client = None
    if any(item.get("type") == "ai" for item in images):
        endpoint = os.environ.get("AOAI_ENDPOINT", "").strip()
        deployment = os.environ.get("AOAI_IMAGE_DEPLOYMENT", "").strip()
        token = os.environ.get("AOAI_TOKEN", "").strip()
        if endpoint and deployment and token:
            image_client = FoundryImageClient(
                endpoint=endpoint,
                deployment=deployment,
                token=token,
                timeout=image_timeout,
            )
        else:
            # Fail-open: without credentials AI body images are skipped (their
            # placeholders are removed), but the run still succeeds.
            warn(
                "AI body images present but AOAI_ENDPOINT/AOAI_IMAGE_DEPLOYMENT/"
                "AOAI_TOKEN are not all set; those placeholders will be removed."
            )

    count = process(
        spec,
        post_path=post_path,
        slug=slug,
        static_images_dir=static_images_dir,
        image_client=image_client,
        downloader=download_allowlisted_image,
        size=size,
        max_bytes=max_bytes,
        download_timeout=download_timeout,
    )
    print(f"Resolved {count} body image(s) into {post_path}")


if __name__ == "__main__":
    main()
