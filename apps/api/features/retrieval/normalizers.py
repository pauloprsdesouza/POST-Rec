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
    }


def normalize_semantic_scholar_paper(paper: dict[str, Any]) -> dict[str, Any] | None:
    title = paper.get("title")
    if not title:
        return None

    authors = [str(a.get("name")) for a in paper.get("authors") or [] if isinstance(a, dict) and a.get("name")]
    external_ids = paper.get("externalIds") or {}
    doi = normalize_doi(external_ids.get("DOI") if isinstance(external_ids, dict) else None)
    url = paper.get("url")
    pdf = nested_get(paper, "openAccessPdf", "url")
    if not url and pdf:
        url = pdf

    return {
        "external_id": paper.get("paperId"),
        "source": "semantic_scholar",
        "title": str(title).strip(),
        "abstract": paper.get("abstract") or None,
        "authors": authors or None,
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "journal_title": paper.get("journal") or paper.get("venue"),
        "issn": None,
        "doi": doi,
        "url": url,
        "citation_count": paper.get("citationCount") or 0,
    }


def normalize_core_work(work: dict[str, Any]) -> dict[str, Any] | None:
    title = work.get("title")
    if not title:
        return None

    authors: list[str] = []
    for author in work.get("authors") or []:
        if not isinstance(author, dict):
            continue
        name = author.get("name")
        if name:
            authors.append(str(name).strip())

    year = work.get("yearPublished")
    if year is None:
        published = work.get("publishedDate")
        if published and str(published)[:4].isdigit():
            year = int(str(published)[:4])

    venue = None
    journal_title = None
    issn = None
    journals = work.get("journals") or []
    if isinstance(journals, list) and journals:
        first = journals[0]
        if isinstance(first, dict):
            venue = first.get("title") or first.get("name")
            journal_title = venue
            issn = normalize_issn(first.get("issn")) or extract_issn_from_list(first.get("identifiers"))

    doi = normalize_doi(work.get("doi"))
    external_id = work.get("id")
    download_url = work.get("downloadUrl")
    url = download_url or (f"https://doi.org/{doi}" if doi else None)

    return {
        "external_id": str(external_id) if external_id is not None else doi,
        "source": "core",
        "title": str(title).strip(),
        "abstract": work.get("abstract") or None,
        "authors": authors or None,
        "year": year,
        "venue": venue,
        "journal_title": journal_title,
        "issn": issn,
        "doi": doi,
        "url": url,
        "citation_count": work.get("citationCount") or 0,
    }


def normalize_crossref_work(item: dict[str, Any]) -> dict[str, Any] | None:
    titles = item.get("title") or []
    title = titles[0] if titles else None
    if not title:
        return None

    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        given = author.get("given") or ""
        family = author.get("family") or ""
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)

    year = None
    for date_key in ("published-print", "published-online", "created"):
        parts = nested_get(item, date_key, "date-parts", default=[])
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = parts[0][0]
            break

    venue_parts = item.get("container-title") or []
    venue = venue_parts[0] if venue_parts else None
    doi = normalize_doi(item.get("DOI"))
    issn = extract_issn_from_list(item.get("ISSN"))

    return {
        "external_id": doi or item.get("URL"),
        "source": "crossref",
        "title": str(title).strip(),
        "abstract": strip_crossref_abstract(item.get("abstract")),
        "authors": authors or None,
        "year": year,
        "venue": venue,
        "journal_title": venue,
        "issn": issn,
        "doi": doi,
        "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
        "citation_count": item.get("is-referenced-by-count") or 0,
    }


def strip_crossref_abstract(abstract: Any) -> str | None:
    if not abstract:
        return None
    text = str(abstract)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


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


# Backward-compatible aliases for tests and deferred imports.
_content_hash = content_hash
_normalize_doi = normalize_doi
_nested_get = nested_get
_normalize_openalex_work = normalize_openalex_work
_normalize_semantic_scholar_paper = normalize_semantic_scholar_paper
_normalize_core_work = normalize_core_work
_normalize_crossref_work = normalize_crossref_work
_strip_crossref_abstract = strip_crossref_abstract
_reconstruct_abstract = reconstruct_abstract
