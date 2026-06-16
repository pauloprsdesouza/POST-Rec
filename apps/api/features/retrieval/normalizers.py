"""Normalize raw API payloads into canonical paper dicts."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def content_hash(title: str, abstract: str | None) -> str:
    content = f"{title}|{abstract or ''}"
    return hashlib.sha256(content.encode()).hexdigest()


def normalize_issn(issn: Any) -> str | None:
    if not issn:
        return None
    from apps.api.features.qualis.normalize import normalize_issn as _normalize_issn

    return _normalize_issn(str(issn))


def extract_issn_from_list(values: Any) -> str | None:
    if not isinstance(values, list):
        return normalize_issn(values)
    for item in values:
        normalized = normalize_issn(item)
        if normalized:
            return normalized
    return None


def normalize_doi(doi: Any) -> str | None:
    if not doi:
        return None
    value = str(doi).strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value or None


def nested_get(data: Any, *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def normalize_openalex_work(work: dict[str, Any]) -> dict[str, Any] | None:
    title = work.get("title") or work.get("display_name")
    if not title:
        return None

    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        name = nested_get(authorship, "author", "display_name")
        if name:
            authors.append(str(name))

    inverted_index = work.get("abstract_inverted_index")
    abstract = reconstruct_abstract(inverted_index) if isinstance(inverted_index, dict) else None

    source = nested_get(work, "primary_location", "source") or {}
    issn = normalize_issn(source.get("issn_l")) if isinstance(source, dict) else None
    if not issn and isinstance(source, dict):
        issn = extract_issn_from_list(source.get("issn"))
    journal_title = source.get("display_name") if isinstance(source, dict) else None

    primary_topic = work.get("primary_topic") if isinstance(work.get("primary_topic"), dict) else {}
    openalex_topics = [
        item.get("display_name")
        for item in (work.get("topics") or [])
        if isinstance(item, dict) and item.get("display_name")
    ]
    open_access = work.get("open_access") if isinstance(work.get("open_access"), dict) else {}
    keywords = [
        item.get("display_name") or item.get("keyword")
        for item in (work.get("keywords") or [])
        if isinstance(item, dict) and (item.get("display_name") or item.get("keyword"))
    ]
    referenced = work.get("referenced_works") or []
    related = work.get("related_works") or []

    return {
        "external_id": work.get("id"),
        "source": "openalex",
        "title": str(title).strip(),
        "abstract": abstract or None,
        "authors": authors or None,
        "year": work.get("publication_year"),
        "venue": journal_title or nested_get(work, "primary_location", "source", "display_name"),
        "journal_title": journal_title,
        "issn": issn,
        "doi": normalize_doi(work.get("doi")),
        "url": work.get("id") or work.get("doi"),
        "citation_count": work.get("cited_by_count") or 0,
        "work_type": work.get("type"),
        "openalex_primary_topic": primary_topic.get("display_name") if primary_topic else None,
        "openalex_field": nested_get(primary_topic, "field", "display_name"),
        "openalex_subfield": nested_get(primary_topic, "subfield", "display_name"),
        "openalex_topics": openalex_topics or None,
        "openalex_fwci": work.get("fwci"),
        "is_open_access": open_access.get("is_oa") if open_access else None,
        "open_access_status": open_access.get("oa_status") if open_access else None,
        "openalex_keywords": keywords or None,
        "openalex_referenced_works": referenced[:20] if isinstance(referenced, list) else None,
        "openalex_related_works": related[:20] if isinstance(related, list) else None,
    }


def reconstruct_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            words.append((pos, word))
    words.sort()
    return " ".join(w for _, w in words)


# Backward-compatible aliases for tests.
_normalize_doi = normalize_doi
_normalize_openalex_work = normalize_openalex_work
_reconstruct_abstract = reconstruct_abstract
