#!/usr/bin/env python3
"""Generate a CODERTECTURA blog post draft with Azure AI Foundry (text only).

Increment 1 of the AI article pipeline: text generation -> assemble a Hugo post
-> (the workflow then opens a PR). No image generation happens here.

Design notes
------------
* The script NEVER calls the Azure CLI. The workflow acquires a data-plane
  bearer token (``az account get-access-token``) and passes it in via the
  ``AOAI_TOKEN`` environment variable. Keeping token acquisition out of the
  script makes it locally testable and keeps the secret out of argv.
* The model output is treated as UNTRUSTED: the JSON is parsed defensively,
  the slug is sanitised to ``[a-z0-9-]`` and the front matter is serialised
  with ``yaml.safe_dump`` (never string-concatenated), so model content cannot
  break out of the YAML block.
* On any API/parse/validation error the script exits non-zero with a clear,
  secret-free message. The bearer token is never printed.

Inputs (environment variables; CLI flags override where provided)
-----------------------------------------------------------------
ARTICLE_TOPIC / --topic       Required. The topic to write about (Spanish).
AOAI_ENDPOINT / --endpoint    Foundry endpoint, e.g.
                              https://asi-relv-blog.services.ai.azure.com/
AOAI_TEXT_DEPLOYMENT          Text deployment name, e.g. gpt-5.4-mini.
  / --deployment
AOAI_TOKEN                    Required. Pre-acquired bearer token (env ONLY).
POSTS_DIR / --posts-dir       Output directory. Default: content/posts.
AOAI_MAX_COMPLETION_TOKENS    Output budget. Default: 16000 (gpt-5.x reasoning
                              models bill reasoning + completion against this).
AOAI_TIMEOUT                  HTTP timeout in seconds. Default: 300.

Outputs
-------
* Writes ``<posts-dir>/<slug>.md``.
* Prints the relative path and slug.
* If ``GITHUB_OUTPUT`` is set, appends ``slug=`` and ``path=`` for the workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone

import yaml

# Version of the editorial prompt below. Stored in the post's `ai.prompt_version`
# for provenance/auditing. Bump it whenever the prompt/voice changes.
PROMPT_VERSION = "2026-06-23.1"

# Honest disclosure string, kept in sync with the archetype and hugo.yaml
# (params.ai.defaultDisclosure).
DISCLOSURE = "AI-assisted draft; reviewed by a human before publication."

# -----------------------------------------------------------------------------
# Editorial system prompt — FIRST DRAFT. This encodes the blog voice and the
# strict JSON contract. Expect to iterate on it after reviewing the first
# generated articles.
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """\
Eres el asistente editorial de CODERTECTURA, un blog técnico en español (España) \
sobre arquitectura de software, desarrollo con .NET, el ecosistema de Microsoft, \
Azure e Inteligencia Artificial.

Voz y estilo:
- Escribe en español de España usando la primera persona del plural ("veamos", \
"analicemos", "os mostramos"), con un tono editorial cercano y de comunidad técnica.
- Dirígete al lector de "vosotros" cuando proceda ("habréis visto", "podéis").
- Técnico pero accesible: explica el "porqué" antes que el "cómo", con ejemplos concretos.
- Rigor: no inventes datos, cifras, citas, nombres de API, versiones ni URLs. Si no \
estás seguro de un detalle, mantente en lo general y verificable.
- Markdown limpio: subtítulos con "###", párrafos cortos, listas y bloques de código \
con el lenguaje indicado cuando aporten valor. No incluyas el título como encabezado \
H1 (Hugo lo renderiza a partir del front matter). No incluyas front matter.
- Emojis: ocasionales y con mesura, solo si encajan con el tono del blog.

Devuelve EXCLUSIVAMENTE un objeto JSON valido (sin vallas de codigo), con EXACTAMENTE \
estas claves:
- "title": titular atractivo en español (sin comillas envolventes).
- "slug": kebab-case ASCII derivado del título (minúsculas, solo [a-z0-9-]).
- "description": 1-2 frases (idealmente <=160 caracteres) para la meta-descripción y \
las tarjetas; texto plano, sin Markdown.
- "tags": lista de 3 a 6 etiquetas en español.
- "categories": lista de 1 a 3 categorías en español coherentes con el blog \
(por ejemplo "Inteligencia Artificial", "Arquitectura de Software", ".NET", "Azure").
- "body_markdown": el artículo completo en Markdown (aproximadamente 800-1500 \
palabras), empezando por un párrafo de introducción que enganche.

No añadas claves adicionales ni ningún texto fuera del objeto JSON.\
"""


def fail(message: str) -> "None":
    """Print a secret-free error to stderr and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    """Print a non-fatal warning to stderr (visible in the Actions log)."""
    print(f"WARNING: {message}", file=sys.stderr)


def slugify(value: str) -> str:
    """Lowercase ASCII slug limited to [a-z0-9-] (Spanish accents transliterated)."""
    normalised = unicodedata.normalize("NFKD", value)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    collapsed = re.sub(r"-{2,}", "-", hyphenated)
    return collapsed.strip("-")


def require_str(payload: dict, key: str) -> str:
    """Return a non-empty trimmed string for ``key`` or fail."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"model response is missing a valid '{key}' field")
    return value.strip()


def clean_terms(raw: object, *, cap: int) -> list:
    """Coerce model-provided tags/categories into a clean, de-duplicated list."""
    cleaned: list = []
    seen: set = set()
    if isinstance(raw, list):
        for item in raw:
            text = item if isinstance(item, str) else str(item)
            normalised = " ".join(text.split()).strip()
            if not normalised:
                continue
            key = normalised.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(normalised)
            if len(cleaned) >= cap:
                break
    return cleaned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Hugo blog post draft via Azure AI Foundry (text only)."
    )
    parser.add_argument("--topic", default=os.environ.get("ARTICLE_TOPIC"))
    parser.add_argument("--endpoint", default=os.environ.get("AOAI_ENDPOINT"))
    parser.add_argument("--deployment", default=os.environ.get("AOAI_TEXT_DEPLOYMENT"))
    parser.add_argument("--posts-dir", default=os.environ.get("POSTS_DIR", "content/posts"))
    return parser.parse_args()


def call_foundry(
    *,
    endpoint: str,
    deployment: str,
    token: str,
    topic: str,
    max_completion_tokens: int,
    timeout: float,
) -> dict:
    """Call the Foundry v1 chat completions endpoint and return the parsed JSON object.

    The bearer token is only ever used in the Authorization header; it is never
    printed or returned.
    """
    url = f"{endpoint.rstrip('/')}/openai/v1/chat/completions"
    request_body = {
        "model": deployment,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Escribe un artículo completo para el blog sobre el siguiente "
                    f"tema:\n\n{topic}\n\n"
                    "Responde únicamente con el objeto JSON especificado."
                ),
            },
        ],
        # gpt-5.x are reasoning models: they require max_completion_tokens
        # (max_tokens is rejected).
        "max_completion_tokens": max_completion_tokens,
        # Force a strict JSON object response.
        "response_format": {"type": "json_object"},
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "codertectura-article-bot/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            # The response body is model/API output (no secrets) -> safe to show
            # a short snippet for diagnostics.
            body = exc.read().decode("utf-8", "replace")[:800]
        except Exception:  # noqa: BLE001 - diagnostics only, never fatal here
            body = "(no response body)"
        fail(
            f"Foundry inference failed with HTTP {exc.code}. "
            f"Endpoint/deployment: {url} / {deployment}. Response snippet: {body}"
        )
    except urllib.error.URLError as exc:
        fail(f"could not reach Foundry endpoint {url}: {exc.reason}")

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        fail("Foundry returned a non-JSON HTTP body (could not decode the envelope)")

    choices = envelope.get("choices") or []
    if not choices:
        fail("Foundry response contained no choices")

    first = choices[0]
    finish_reason = first.get("finish_reason")
    content = (first.get("message") or {}).get("content")
    if not isinstance(content, str) or not content.strip():
        fail(
            "Foundry response had empty message content "
            f"(finish_reason={finish_reason!r}); try a larger AOAI_MAX_COMPLETION_TOKENS"
        )

    if finish_reason == "length":
        warn(
            "the model output was truncated (finish_reason=length); the article may be "
            "incomplete. Consider increasing AOAI_MAX_COMPLETION_TOKENS."
        )

    try:
        article = json.loads(content)
    except json.JSONDecodeError:
        fail("the model did not return valid JSON in its message content")

    if not isinstance(article, dict):
        fail("the model JSON was not an object")

    return article


def build_document(article: dict, *, deployment: str, now_iso: str) -> "tuple[str, str]":
    """Validate the model output and return (slug, full markdown document)."""
    title = require_str(article, "title")
    description = require_str(article, "description")
    body_markdown = require_str(article, "body_markdown")

    slug = slugify(article.get("slug") or "") or slugify(title)
    if not slug:
        fail("could not derive a valid slug from the model 'slug' or 'title'")
    slug = slug[:80].strip("-")

    categories = clean_terms(article.get("categories"), cap=3)
    tags = clean_terms(article.get("tags"), cap=6)
    if not categories:
        warn("model returned no usable categories; the draft will have an empty list")
    if not tags:
        warn("model returned no usable tags; the draft will have an empty list")

    front_matter = {
        "title": title,
        "date": now_iso,
        "draft": True,
        "slug": slug,
        "description": description,
        "categories": categories,
        "tags": tags,
        # Increment 1 produces no cover image. The theme treats an empty string
        # as "no image", a valid draft state.
        "image": "",
        "comments": True,
        "ai": {
            "assisted": True,
            "model": deployment,
            "prompt_version": PROMPT_VERSION,
            "generated_at": now_iso,
            "reviewed_by": "",
            "review_status": "pending",
            "disclosure": DISCLOSURE,
        },
    }

    yaml_block = yaml.safe_dump(
        front_matter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()

    document = f"---\n{yaml_block}\n---\n\n{body_markdown.strip()}\n"
    return slug, document


def main() -> None:
    args = parse_args()

    topic = (args.topic or "").strip()
    if not topic:
        fail("no topic provided (set ARTICLE_TOPIC or pass --topic)")

    endpoint = (args.endpoint or "").strip()
    if not endpoint:
        fail("no Foundry endpoint provided (set AOAI_ENDPOINT or pass --endpoint)")

    deployment = (args.deployment or "").strip()
    if not deployment:
        fail("no deployment provided (set AOAI_TEXT_DEPLOYMENT or pass --deployment)")

    token = os.environ.get("AOAI_TOKEN", "").strip()
    if not token:
        fail("no bearer token provided (set AOAI_TOKEN; never pass it on the command line)")

    try:
        max_completion_tokens = int(os.environ.get("AOAI_MAX_COMPLETION_TOKENS", "16000"))
    except ValueError:
        fail("AOAI_MAX_COMPLETION_TOKENS must be an integer")
    try:
        timeout = float(os.environ.get("AOAI_TIMEOUT", "300"))
    except ValueError:
        fail("AOAI_TIMEOUT must be a number (seconds)")

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    article = call_foundry(
        endpoint=endpoint,
        deployment=deployment,
        token=token,
        topic=topic,
        max_completion_tokens=max_completion_tokens,
        timeout=timeout,
    )

    slug, document = build_document(article, deployment=deployment, now_iso=now_iso)

    posts_dir = args.posts_dir.strip() or "content/posts"
    rel_path = f"{posts_dir.rstrip('/')}/{slug}.md"
    out_path = os.path.join(posts_dir, f"{slug}.md")

    if os.path.exists(out_path):
        fail(
            f"refusing to overwrite existing file: {rel_path}. "
            "Pick a different topic or remove the existing draft."
        )

    os.makedirs(posts_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(document)

    print(f"Generated article: {rel_path}")
    print(f"slug={slug}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"slug={slug}\n")
            handle.write(f"path={rel_path}\n")


if __name__ == "__main__":
    main()
