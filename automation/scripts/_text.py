#!/usr/bin/env python3
"""Shared text helpers for CODERTECTURA automation scripts."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: object) -> str:
    """Return an ASCII lowercase slug limited to ``[a-z0-9-]``."""
    if not isinstance(value, str):
        return ""
    normalised = unicodedata.normalize("NFKD", value)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    hyphenated = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())
    return re.sub(r"-{2,}", "-", hyphenated).strip("-")