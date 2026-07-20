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

import json
import os
import sys
from typing import NoReturn

from _foundry import FoundryError, FoundryImageClient

# Covers use article-specific artistic art direction. This suffix enforces the
# painterly medium, contemporary grounding, full-bleed composition, crop resilience
# and safety; it must not impose a recurring scene, subject, palette or lighting
# recipe. It intentionally diverges from the schematic BODY_STYLE_SUFFIX in
# resolve_body_images.py.
STYLE_SUFFIX = (
    " -- evocative editorial cover art for a professional technology publication, "
    "executed as a cinematic digital painting / concept-art illustration: visible "
    "painterly brushwork, rich texture and atmospheric depth. NOT a photograph, NOT "
    "photorealistic, NOT a sterile 3D product render or industrial advertising shot. "
    "The scene MUST stay grounded in the CONTEMPORARY world of software and "
    "technology: modern people, present-day devices and workplaces, cloud and code "
    "concepts, or abstract flows of light and data. Strictly avoid fantasy, "
    "fairy-tale, steampunk, medieval, retro-antique or alchemical imagery: no old "
    "workshops, brass contraptions, parchment scrolls, magical artifacts, wizards or "
    "toy automatons. Preserve the article-specific concept, subject, setting and "
    "meaningful colour palette from the brief; do not replace them with generic "
    "imagery. Dramatic, expressive lighting with one clear focal point is welcome "
    "(for example a warm glow against deep cool blues); render any people as "
    "stylised figures or silhouettes, never detailed realistic faces. Communicate "
    "one idea immediately at thumbnail size with confident visual hierarchy, and "
    "keep the essential subject and metaphor within the central 70% safe area so "
    "the image survives wide 2:1 LinkedIn and blog-card crops. Paint the FULL "
    "canvas edge to edge as one continuous scene: absolutely no empty bars, flat "
    "borders, letterboxing or unfinished areas; make the lower portion of the "
    "scene quieter and less detailed (floor, water, mist, shadow) so a title can "
    "be overlaid, but keep it fully painted as part of the scene. No baked-in "
    "text, letters, numbers or watermarks, and no recognisable real human faces. "
    "Relevant product logos or brands are allowed only when requested by the "
    "supplied brief."
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


def _write_debug_json(path: str, payload: dict) -> None:
    """Persist a debug JSON payload (best effort, never raises)."""
    if not path:
        return
    try:
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Wrote image debug trace: {path}")
    except OSError as exc:
        print(f"WARNING: could not write IMAGE_DEBUG_FILE ({path}): {exc}", file=sys.stderr)


def _env_truthy(name: str, default: bool = False) -> bool:
    """Interpret an env var as boolean (1/true/yes/on)."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _emit_image_trace(payload: dict) -> None:
    """Emit image-generation traces to stdout for Actions/Copilot UI."""
    print("::group::AI TRACE - image prompts")
    print("BASE_PROMPT:")
    print(payload.get("base_prompt", ""))
    print("\nSTYLE_SUFFIX:")
    print(payload.get("style_suffix", ""))
    print("\nFINAL_PROMPT:")
    print(payload.get("final_prompt", ""))
    print("::endgroup::")

    print("::group::AI TRACE - image summary")
    summary = {
        "deployment": payload.get("deployment"),
        "size": payload.get("size"),
        "cover_path": payload.get("cover_path"),
        "output_bytes": payload.get("output_bytes"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("::endgroup::")


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

    image_debug_file = os.environ.get("IMAGE_DEBUG_FILE", "").strip()
    trace_stdout = _env_truthy("IMAGE_TRACE_STDOUT", default=False)

    base_prompt = read_prompt()
    prompt = base_prompt + STYLE_SUFFIX

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

    _write_debug_json(
        image_debug_file,
        {
            "endpoint": endpoint,
            "deployment": deployment,
            "size": size,
            "timeout": timeout,
            "cover_path": cover_path,
            "base_prompt": base_prompt,
            "style_suffix": STYLE_SUFFIX,
            "final_prompt": prompt,
            "output_bytes": len(image_bytes),
        },
    )
    if trace_stdout:
        _emit_image_trace(
            {
                "deployment": deployment,
                "size": size,
                "cover_path": cover_path,
                "base_prompt": base_prompt,
                "style_suffix": STYLE_SUFFIX,
                "final_prompt": prompt,
                "output_bytes": len(image_bytes),
            }
        )

    print(f"Generated cover image: {cover_path} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    main()
