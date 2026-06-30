#!/usr/bin/env python3
"""Shared Azure AI Foundry helpers for the CODERTECTURA automation scripts.

This small module factors out the genuinely reusable pieces of the AI pipeline:

* a chat-completions client that supports **tool calling** (used by the agentic
  news-discovery loop now, and available to the article generator later),
* an **injectable** embeddings client (so offline tests can mock it with no
  network), and
* the HTTP / token plumbing that both share.

Design constraints (kept in lockstep with ``generate_article.py``):

* **Standard library only** plus PyYAML elsewhere. The HTTP calls use ``urllib``;
  cosine similarity is a few lines of arithmetic (no numpy).
* The scripts NEVER call the Azure CLI. A pre-acquired data-plane bearer token is
  passed in by the caller (workflow env ``AOAI_TOKEN``); token acquisition stays
  out of the scripts so they are locally testable and the secret never reaches
  argv.
* The bearer token (and any API key) is ONLY ever placed in the ``Authorization``
  header. It is never printed, returned, or written to outputs. HTTP errors only
  surface the response body (model/API output, no secrets) and the URL.
"""

from __future__ import annotations

import base64
import binascii
import json
import math
import sys
import urllib.error
import urllib.request
from typing import Mapping, Sequence

# User-Agent sent on every Foundry request (diagnostics only; carries no secret).
USER_AGENT = "codertectura-automation-bot/1.0"

# MAI-Image-2.5 is a Microsoft first-party model served on the "/mai/v1/" surface
# (NOT "/openai/v1/", which is Azure OpenAI and returns {"code":"unknown_model"}
# for this model). The surface accepts a Microsoft Entra ID (OIDC/UAMI) token, so
# no API key is needed and no api-version query string is required.
#IMAGE_API_PATH = "/mai/v1/images/generations"

# OpenAI gpt-image-2
IMAGE_API_PATH = "/openai/v1/images/generations"

class FoundryError(RuntimeError):
    """Raised on any Foundry/HTTP/parse failure with a secret-free message."""


def fail(message: str) -> "None":
    """Print a secret-free error to stderr and exit non-zero.

    Mirrors the helper in ``generate_article.py`` so the scripts behave
    identically when something goes wrong.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    """Print a non-fatal warning to stderr (visible in the Actions log)."""
    print(f"WARNING: {message}", file=sys.stderr)


def http_post_json(
    url: str,
    payload: Mapping[str, object],
    *,
    headers: Mapping[str, str],
    timeout: float,
) -> dict:
    """POST ``payload`` as JSON and return the parsed JSON response.

    ``headers`` is supplied in full by the caller (including any ``Authorization``
    header), so this helper never has to know about a specific credential and the
    secret never leaks into error messages: only the response body and URL — which
    contain no secrets — are surfaced on failure.
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)

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
        raise FoundryError(
            f"HTTP {exc.code} from {url}. Response snippet: {snippet}"
        ) from exc
    except urllib.error.URLError as exc:
        raise FoundryError(f"could not reach {url}: {exc.reason}") from exc

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FoundryError(f"non-JSON HTTP body from {url}") from exc

    if not isinstance(envelope, dict):
        raise FoundryError(f"unexpected (non-object) JSON body from {url}")
    return envelope


class FoundryChatClient:
    """Minimal chat-completions client for the Foundry ``/openai/v1`` surface.

    Supports tool calling: pass ``tools`` (and optionally ``tool_choice``) and read
    ``tool_calls`` off the returned assistant message to drive a ReAct loop.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        token: str,
        timeout: float = 120.0,
    ) -> None:
        self._url = f"{endpoint.rstrip('/')}/openai/v1/chat/completions"
        self._deployment = deployment
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def complete(
        self,
        messages: Sequence[Mapping[str, object]],
        *,
        tools: "Sequence[Mapping[str, object]] | None" = None,
        tool_choice: "object | None" = None,
        response_format: "Mapping[str, object] | None" = None,
        max_completion_tokens: int = 8000,
    ) -> dict:
        """Call chat completions once and return ``{"message", "finish_reason"}``.

        ``gpt-5.x`` are reasoning models: they require ``max_completion_tokens``
        (``max_tokens`` is rejected).
        """
        body: dict = {
            "model": self._deployment,
            "messages": list(messages),
            "max_completion_tokens": max_completion_tokens,
        }
        if tools:
            body["tools"] = list(tools)
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        if response_format is not None:
            body["response_format"] = response_format

        envelope = http_post_json(
            self._url, body, headers=self._headers, timeout=self._timeout
        )

        choices = envelope.get("choices") or []
        if not choices:
            raise FoundryError("Foundry chat response contained no choices")
        first = choices[0] or {}
        message = first.get("message")
        if not isinstance(message, dict):
            raise FoundryError("Foundry chat response had no assistant message")
        return {"message": message, "finish_reason": first.get("finish_reason")}


class FoundryImageClient:
    """Image-generation client for the Foundry MAI ``/mai/v1`` surface.

    Shared by ``generate_image.py`` (cover image) and ``resolve_body_images.py``
    (in-body AI illustrations) so the MAI call lives in exactly one place. The
    bearer token is only ever placed in the ``Authorization`` header; it is never
    printed or returned. ``generate`` returns the raw image bytes and raises
    :class:`FoundryError` on any API/decode/download failure so callers can decide
    whether to fail closed (cover) or fail open (best-effort body images).
    """

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        token: str,
        timeout: float = 300.0,
    ) -> None:
        self._url = f"{endpoint.rstrip('/')}{IMAGE_API_PATH}"
        self._deployment = deployment
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        output_compression: int = 100,
    ) -> bytes:
        """Generate one image for ``prompt`` and return its raw bytes."""
        body = {
            "model": self._deployment,
            "prompt": prompt,
            "n": 1,
            "size": size,
            # MAI-Image-2.5 returns the image inline as base64; request PNG
            # explicitly (mirrors the Foundry Playground call for this resource).
            "output_format": "png",
            "output_compression": output_compression,
        }
        envelope = http_post_json(
            self._url, body, headers=self._headers, timeout=self._timeout
        )
        return self._extract_image_bytes(envelope)

    def _extract_image_bytes(self, envelope: dict) -> bytes:
        """Return image bytes from a MAI image response (``b64_json`` or ``url``)."""
        data = envelope.get("data") or []
        if not data:
            raise FoundryError("image response contained no data")

        first = data[0] or {}

        encoded = first.get("b64_json")
        if isinstance(encoded, str) and encoded:
            try:
                # Default (validate=False) tolerates whitespace in the payload.
                return base64.b64decode(encoded)
            except (binascii.Error, ValueError) as exc:
                raise FoundryError("could not decode the base64 image payload") from exc

        # Some responses return a short-lived, Foundry-issued download URL instead
        # of inline base64. That URL is produced by the trusted image API (not by
        # the model), so it is safe to fetch directly.
        url = first.get("url")
        if isinstance(url, str) and url:
            try:
                with urllib.request.urlopen(url, timeout=self._timeout) as response:
                    return response.read()
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                raise FoundryError(f"could not download the generated image: {exc}") from exc

        raise FoundryError("image response had neither 'b64_json' nor 'url'")


class EmbeddingsClient:
    """Injectable embeddings interface.

    Production code uses :class:`FoundryEmbeddingsClient`; tests inject a fake so
    no network call happens. Implementations return one vector per input text, in
    the same order as the inputs.
    """

    def embed(self, texts: Sequence[str]) -> "list[list[float]]":
        raise NotImplementedError


class FoundryEmbeddingsClient(EmbeddingsClient):
    """Embeddings client backed by the Foundry ``/openai/v1/embeddings`` surface."""

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        token: str,
        timeout: float = 60.0,
        batch_size: int = 64,
    ) -> None:
        self._url = f"{endpoint.rstrip('/')}/openai/v1/embeddings"
        self._deployment = deployment
        self._timeout = timeout
        self._batch_size = max(1, batch_size)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def embed(self, texts: Sequence[str]) -> "list[list[float]]":
        items = list(texts)
        if not items:
            return []

        vectors: "list[list[float]]" = []
        for start in range(0, len(items), self._batch_size):
            chunk = items[start : start + self._batch_size]
            body = {"model": self._deployment, "input": chunk}
            envelope = http_post_json(
                self._url, body, headers=self._headers, timeout=self._timeout
            )
            data = envelope.get("data")
            if not isinstance(data, list) or len(data) != len(chunk):
                raise FoundryError(
                    "unexpected embeddings response shape (data length mismatch)"
                )
            # Defensively restore input order using the per-item 'index'.
            ordered = sorted(
                data,
                key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0,
            )
            for item in ordered:
                vector = item.get("embedding") if isinstance(item, dict) else None
                if not isinstance(vector, list) or not vector:
                    raise FoundryError("embeddings response item had no vector")
                try:
                    vectors.append([float(value) for value in vector])
                except (TypeError, ValueError) as exc:
                    raise FoundryError("embedding vector was not numeric") from exc
        return vectors


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the cosine similarity of two equal-length vectors in ``[-1, 1]``.

    Returns ``0.0`` for empty, mismatched-length, or zero-magnitude vectors
    (treated as "not similar") rather than raising, so callers can stay simple.
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
