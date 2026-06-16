"""Normalization helpers for Qualis journal matching."""

from __future__ import annotations

import re
import unicodedata

ISSN_PATTERN = re.compile(r"[^0-9Xx]")
NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_issn(value: str | None) -> str | None:
    """Normalize ISSN to XXXX-XXXX (uppercase check digit)."""
    if not value:
        return None
    cleaned = ISSN_PATTERN.sub("", str(value).strip().upper())
    if len(cleaned) != 8:
        return None
    return f"{cleaned[:4]}-{cleaned[4:]}"


def normalize_title(value: str | None) -> str | None:
    if not value:
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = NON_ALNUM.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper() if text else None
