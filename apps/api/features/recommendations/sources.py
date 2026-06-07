"""Helpers to resolve retrieved sources for recommendations."""

from apps.api.shared.models import RecommendationRunEvent, SourceDocument
from apps.api.shared.schemas.common import SourceDocumentResponse


def serialize_source_documents(documents: list[SourceDocument]) -> list[dict]:
    return [
        SourceDocumentResponse(
            id=d.id,
            source=d.source,
            title=d.title,
            abstract=d.abstract,
            authors=d.authors,
            year=d.year,
            venue=d.venue,
            doi=d.doi,
            url=d.url,
            citation_count=d.citation_count or 0,
        ).model_dump(mode="json")
        for d in documents
    ]


def get_run_source_documents(db, run_id) -> list[SourceDocument]:
    event = (
        db.query(RecommendationRunEvent)
        .filter_by(run_id=run_id, event_type="papers_retrieved")
        .order_by(RecommendationRunEvent.created_at.desc())
        .first()
    )
    if not event or not event.payload:
        return []

    doc_ids = event.payload.get("document_ids") or []
    if not doc_ids:
        return []

    return db.query(SourceDocument).filter(SourceDocument.id.in_(doc_ids)).all()


def build_source_lookup(documents: list[SourceDocument]) -> tuple[dict, dict]:
    by_doi: dict[str, SourceDocument] = {}
    by_title: dict[str, SourceDocument] = {}
    for doc in documents:
        if doc.doi:
            by_doi[str(doc.doi).lower()] = doc
        by_title[doc.title.lower().strip()] = doc
    return by_doi, by_title


def enrich_evidence_papers(evidence_papers: list | None, documents: list[SourceDocument]) -> list[dict]:
    if not evidence_papers:
        return []

    by_doi, by_title = build_source_lookup(documents)
    enriched: list[dict] = []

    for item in evidence_papers:
        if not isinstance(item, dict):
            continue

        doi = (item.get("doi") or "").lower().replace("https://doi.org/", "")
        title_key = (item.get("title") or "").lower().strip()
        matched = by_doi.get(doi) if doi else by_title.get(title_key)

        entry = {
            "title": item.get("title"),
            "year": item.get("year"),
            "doi": item.get("doi"),
            "url": item.get("url"),
            "why_relevant": item.get("why_relevant"),
            "retrieval_source": matched.source if matched else None,
            "citation_count": matched.citation_count if matched else None,
            "venue": matched.venue if matched else None,
            "abstract": matched.abstract if matched else None,
            "matched_in_catalog": matched is not None,
        }
        if matched and not entry["url"]:
            entry["url"] = matched.url
        enriched.append(entry)

    return enriched
