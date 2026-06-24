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

import base64
import binascii
import json
import os
import sys
import urllib.error
import urllib.request
from typing import NoReturn

# MAI-Image-2.5 is a Microsoft first-party model, served on the "/mai/v1/" surface
# (NOT "/openai/v1/", which is Azure OpenAI and returns {"code":"unknown_model"} for
# this model). This surface accepts a Microsoft Entra ID (OIDC/UAMI) token, so no API
# key is needed. No api-version query string is required.
IMAGE_API_PATH = "/mai/v1/images/generations"
IMAGE_API_QUERY = ""

# Fixed style wrapper appended to every prompt so covers stay visually consistent
# across posts. Deliberately generic and text/logo-free (text in generated images
# tends to render poorly).
STYLE_SUFFIX = (
    " -- wide editorial blog cover illustration, modern and clean, conceptual "
    "technology theme, soft gradients, blue and teal palette, subtle geometric "
    "shapes, high quality, no text, no letters, no logos, no watermarks"
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


def request_image(
    *,
    endpoint: str,
    deployment: str,
    token: str,
    prompt: str,
    size: str,
    timeout: float,
) -> dict:
    """Call the Foundry v1 image-generation endpoint and return the parsed JSON."""
    url = f"{endpoint.rstrip('/')}{IMAGE_API_PATH}{IMAGE_API_QUERY}"
    body = {
        "model": deployment,
        "prompt": prompt,
        "n": 1,
        "size": size,
        # MAI-Image-2.5 returns the image inline as base64; request PNG explicitly
        # (mirrors the Foundry Playground call for this resource).
        "output_format": "png",
        "output_compression": 100,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        snippet = ""
        try:
            # The body is API/model output (no secrets) -> safe to show a snippet.
            snippet = exc.read().decode("utf-8", "replace")[:800]
        except Exception:  # noqa: BLE001 - diagnostics only, never fatal here
            snippet = "(no response body)"
        fail(
            f"image generation failed with HTTP {exc.code}. "
            f"Endpoint/deployment: {url} / {deployment}. Response snippet: {snippet}"
        )
    except urllib.error.URLError as exc:
        fail(f"could not reach the image endpoint {url}: {exc.reason}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fail("the image endpoint returned a non-JSON HTTP body")


def extract_image_bytes(envelope: dict, *, timeout: float) -> bytes:
    """Return raw image bytes from a Foundry image response (b64_json or url)."""
    data = envelope.get("data") or []
    if not data:
        fail("image response contained no data")

    first = data[0] or {}

    encoded = first.get("b64_json")
    if isinstance(encoded, str) and encoded:
        try:
            # Default (validate=False) tolerates whitespace/newlines in the payload.
            return base64.b64decode(encoded)
        except (binascii.Error, ValueError):
            fail("could not decode the base64 image payload")

    url = first.get("url")
    if isinstance(url, str) and url:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            fail(f"could not download the generated image: {exc}")

    fail("image response had neither 'b64_json' nor 'url'")


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

    envelope = request_image(
        endpoint=endpoint,
        deployment=deployment,
        token=token,
        prompt=prompt,
        size=size,
        timeout=timeout,
    )

    image_bytes = extract_image_bytes(envelope, timeout=timeout)
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
