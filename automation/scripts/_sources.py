#!/usr/bin/env python3
"""Shared trusted-source policy for the CODERTECTURA automation scripts.

This module is the SINGLE SOURCE OF TRUTH for two security-critical concerns that
several pipeline steps share:

* the **official Microsoft + GitHub domain allowlist** and the host-matching logic
  used to enforce it (defence in depth — every URL is re-checked, never trusted
  just because an upstream step "already validated" it), and
* a small **untrusted-text sanitiser** used to flatten any web-derived text
  (titles, snippets, captions) into a safe, bounded single line before it is shown
  to the model or written into a Hugo shortcode.

It is deliberately ``stdlib``-only and free of any Foundry/HTTP concerns so it can
be imported by the discovery agent, the article generator and the body-image
resolver without pulling in unrelated dependencies.
"""

from __future__ import annotations

import os
import re
from typing import Iterable
from urllib.parse import urlsplit

# -----------------------------------------------------------------------------
# Allowlist. NONE of these may EVER come from model output — they are a
# server-side constant enforced by the orchestrator scripts.
# -----------------------------------------------------------------------------

# The official Microsoft + GitHub domain allowlist. This is the one place the
# allowlist is defined; ``discover_topics.py`` re-imports it so discovery, article
# generation and image extraction can never drift apart.
ALLOWLIST_DOMAINS = (
    "learn.microsoft.com",
    "devblogs.microsoft.com",
    "techcommunity.microsoft.com",
    "azure.microsoft.com",
    "microsoft.com",
    "github.blog",
    "github.com",
    "githubnext.com",
)

# Control characters we strip from untrusted text (everything below 0x20 except
# the ones ``str.split`` already collapses, plus DEL).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def extract_host(url: object) -> str:
    """Return the lowercased hostname of ``url`` without a leading ``www.``.

    ``urlsplit`` only parses; it never executes anything, so this is safe for
    untrusted input. Returns ``""`` for anything that is not a usable URL string.
    """
    if not isinstance(url, str) or not url:
        return ""
    host = (urlsplit(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def host_is_allowed(url_or_host: object) -> bool:
    """True when the URL/host belongs to (a subdomain of) an allowlisted domain.

    Accepts either a full URL (``https://host/path``) or a bare host. The match is
    exact or a dotted-suffix match, so ``api.github.com`` is accepted (subdomain of
    ``github.com``) while suffix-spoofs such as ``microsoft.com.evil.example`` and
    ``github.io`` are rejected.
    """
    candidate = url_or_host if isinstance(url_or_host, str) else ""
    host = extract_host(candidate) if "://" in candidate else candidate.lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return False
    for domain in ALLOWLIST_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return True
    return False


def is_http_url(url: object) -> bool:
    """True only for absolute ``http``/``https`` URLs with a host.

    Used as an SSRF guard before any network fetch so schemes like ``file:``,
    ``ftp:`` or ``data:`` can never reach the downloader.
    """
    if not isinstance(url, str) or not url:
        return False
    parts = urlsplit(url)
    return parts.scheme in ("http", "https") and bool(parts.hostname)


def _image_url_denylist() -> "tuple[str, ...]":
    """Return the lowercased ``IMAGE_URL_DENYLIST`` substrings (env), or ``()``.

    Read fresh on every call so an operator can flip the block purely through the
    environment, with no code change. Empty/unset -> ``()`` (a no-op).
    """
    raw = os.environ.get("IMAGE_URL_DENYLIST", "")
    return tuple(token for token in (part.strip().lower() for part in raw.split(",")) if token)


def is_denylisted_image(url: object) -> bool:
    """True when ``url`` contains any ``IMAGE_URL_DENYLIST`` substring (case-insensitive).

    A tiny, optional post-incident kill-switch for source images: set
    ``IMAGE_URL_DENYLIST`` to a comma-separated list of substrings and any source
    image whose URL contains one of them is refused at the acceptance/download
    gates (defence in depth, on top of the host allowlist). Unset (the default)
    always returns ``False``, so behaviour is unchanged until it is needed.
    """
    if not isinstance(url, str) or not url:
        return False
    denylist = _image_url_denylist()
    if not denylist:
        return False
    lowered = url.lower()
    return any(token in lowered for token in denylist)


def sanitize_untrusted_text(
    value: object,
    *,
    max_length: int = 500,
    forbidden: Iterable[str] = (),
) -> str:
    """Flatten untrusted external text into a safe, bounded single-line string.

    Removes control characters, strips any caller-supplied ``forbidden`` substrings
    (e.g. the delimiter tokens that fence an untrusted block, so results cannot
    forge a block boundary), collapses all whitespace, and truncates to
    ``max_length`` characters.
    """
    text = value if isinstance(value, str) else ("" if value is None else str(value))
    text = _CONTROL_CHARS.sub(" ", text)
    for token in forbidden:
        if token:
            text = text.replace(token, " ")
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length].rstrip() + "…"
    return text


def sanitize_untrusted_excerpt(
    value: object,
    *,
    max_length: int = 1200,
    forbidden: Iterable[str] = (),
) -> str:
    """Flatten untrusted external text into a safe, bounded MULTI-line excerpt.

    Like :func:`sanitize_untrusted_text`, but it preserves single newlines so
    code-ish snippets stay readable for code-example grounding. Each line is
    cleaned individually (control characters and any caller-supplied ``forbidden``
    delimiter tokens removed, intra-line whitespace collapsed); blank lines are
    dropped; the surviving lines are joined with a single ``"\\n"`` and the result
    is truncated to ``max_length`` characters. Used for the per-source ``excerpt``
    that the discovery agent persists and the article generator surfaces.
    """
    text = value if isinstance(value, str) else ("" if value is None else str(value))
    lines: list = []
    for raw_line in text.splitlines():
        line = _CONTROL_CHARS.sub(" ", raw_line)
        for token in forbidden:
            if token:
                line = line.replace(token, " ")
        line = " ".join(line.split())
        if line:
            lines.append(line)
    joined = "\n".join(lines)
    if len(joined) > max_length:
        joined = joined[:max_length].rstrip() + "…"
    return joined
