#!/usr/bin/env python3
"""Generate a cover image for a CODERTECTURA post with Azure AI Foundry.

Increment 2 of the AI article pipeline. Reads the image prompt produced by
``generate_article.py`` and calls the Foundry v1 image-generation API, writing a
PNG to the path given by ``COVER_PATH`` (``static/images/<slug>/cover.png``).

Design notes
------------
* The script NEVER calls the Azure CLI. The workflow acquires a data-plane bearer
  token (``az account get-access-token``) via OIDC/UAMI and passes it in via the
  ``AOAI_TOKEN`` environment variable, so the credential stays out of argv.
* The bearer token is only ever used in the Authorization header; it is never
  printed, exported or written to step outputs/logs.
* The prompt is read from a file (``IMAGE_PROMPT_FILE``) so multi-line text never
  travels through the shell/argv.
* The Foundry response may carry the image inline as ``b64_json`` or as a
  short-lived ``url``; both are handled.
* On any network/parse/validation error the script exits non-zero with a clear,
  secret-free message so the workflow fails CLOSED (no PR without a valid cover).

Inputs (environment variables only)
------------------------------------
AOAI_ENDPOINT           Foundry endpoint, e.g. https://asi-relv-blog.services.ai.azure.com/
AOAI_IMAGE_DEPLOYMENT   Image deployment name, e.g. MAI-Image-2.5.
AOAI_TOKEN              Required. Pre-acquired bearer token (env ONLY).
COVER_PATH             Required. Output file path, e.g. static/images/<slug>/cover.png.
IMAGE_PROMPT_FILE      Path to a UTF-8 file holding the image prompt.
IMAGE_PROMPT           Inline fallback prompt if IMAGE_PROMPT_FILE is absent/empty.
AOAI_IMAGE_SIZE        Image size. Default: 1024x1024.
AOAI_IMAGE_TIMEOUT     HTTP timeout in seconds. Default: 300.

Output
------
* Writes the image bytes to ``COVER_PATH`` (creating parent directories).
* Prints the path and byte count.
"""

from __future__ import annotations

import os
import sys
from typing import NoReturn

from _foundry import FoundryError, FoundryImageClient

# CODERTECTURA cover look (grounded in the logo + site theme) -- now a HIGH-IMPACT,
# cinematic editorial style: a bold conceptual scene built around a clear hero
# subject and a memorable visual metaphor, with dramatic lighting and depth over a
# deep midnight navy-to-black base. NOTE: this INTENTIONALLY diverges from
# resolve_body_images.BODY_STYLE_SUFFIX -- covers are dramatic/cinematic, body images
# stay flat/explanatory diagrams. Do NOT "re-sync" them. Cover-specific: keep the
# lower third calmer/darker so the Hugo title overlay keeps good contrast. Always
# text/letter/logo/brand/watermark-free and free of recognizable real human faces.
STYLE_SUFFIX = (
    " -- dramatic cinematic editorial blog cover, bold high-impact composition "
    "built around a single strong focal subject with a clear visual metaphor, deep "
    "sense of depth and scale (foreground, midground and background), moody "
    "volumetric lighting with atmospheric haze and glowing light rays, rich "
    "contrast and vivid expressive cinematic color over a deep midnight "
    "navy-to-black base, immersive and energetic sci-fi tech atmosphere; allowed "
    "subjects include silhouettes, figures seen from behind and stylised robots or "
    "mascots, human faces as long as they are not recognizable real human faces; keep the lower third calmer and "
    "darker so an overlaid title stays legible, ultra detailed, high quality, "
    "no text, no letters, no numbers, no watermarks. You can use logos or brands as long as they are part of the blog post."
)


def fail(message: str) -> NoReturn:
    """Print a secret-free error to stderr and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_prompt() -> str:
    """Return the image prompt from IMAGE_PROMPT_FILE or IMAGE_PROMPT, or fail."""
    prompt_file = os.environ.get("IMAGE_PROMPT_FILE", "").strip()
    if prompt_file:
        try:
            with open(prompt_file, "r", encoding="utf-8") as handle:
                text = handle.read().strip()
        except OSError as exc:
            fail(f"could not read IMAGE_PROMPT_FILE ({prompt_file}): {exc}")
        if text:
            return text
    inline = os.environ.get("IMAGE_PROMPT", "").strip()
    if inline:
        return inline
    fail("no image prompt provided (set IMAGE_PROMPT_FILE or IMAGE_PROMPT)")


def main() -> None:
    endpoint = os.environ.get("AOAI_ENDPOINT", "").strip()
    if not endpoint:
        fail("no Foundry endpoint provided (set AOAI_ENDPOINT)")

    deployment = os.environ.get("AOAI_IMAGE_DEPLOYMENT", "").strip()
    if not deployment:
        fail("no image deployment provided (set AOAI_IMAGE_DEPLOYMENT)")

    token = os.environ.get("AOAI_TOKEN", "").strip()
    if not token:
        fail("no bearer token provided (set AOAI_TOKEN; never pass it on the command line)")

    cover_path = os.environ.get("COVER_PATH", "").strip()
    if not cover_path:
        fail("no output path provided (set COVER_PATH)")

    size = os.environ.get("AOAI_IMAGE_SIZE", "1024x1024").strip() or "1024x1024"
    try:
        timeout = float(os.environ.get("AOAI_IMAGE_TIMEOUT", "300"))
    except ValueError:
        fail("AOAI_IMAGE_TIMEOUT must be a number (seconds)")

    prompt = read_prompt() + STYLE_SUFFIX

    client = FoundryImageClient(
        endpoint=endpoint,
        deployment=deployment,
        token=token,
        timeout=timeout,
    )
    try:
        image_bytes = client.generate(prompt, size=size)
    except FoundryError as exc:
        # Fail closed: no PR without a valid cover. The message carries no secret
        # (only the endpoint/deployment and the API response snippet).
        fail(
            f"image generation failed. Endpoint/deployment: {endpoint} / {deployment}. {exc}"
        )

    if len(image_bytes) < 100:
        fail("the generated image was unexpectedly small; aborting")

    out_dir = os.path.dirname(cover_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(cover_path, "wb") as handle:
        handle.write(image_bytes)

    print(f"Generated cover image: {cover_path} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    main()
