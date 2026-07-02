"""Helpers to resolve retrieved sources for recommendations."""

from apps.api.shared.models import RecommendationRunEvent, SourceDocument
from apps.api.shared.schemas.common import SourceDocumentResponse


def get_ranked_paper_id_by_document_id(db, run_id) -> dict[str, str]:
    """Map source document IDs to P1..Pn labels from the ranked paper list."""
    event = (
        db.query(RecommendationRunEvent)
        .filter_by(run_id=run_id, event_type="papers_ranked")
        .order_by(RecommendationRunEvent.created_at.desc())
        .first()
    )
    if not event or not isinstance(event.payload, dict):
        return {}

    mapping: dict[str, str] = {}
    for index, item in enumerate(event.payload.get("papers") or []):
        if not isinstance(item, dict):
            continue
        doc_id = item.get("id")
        if doc_id:
            mapping[str(doc_id)] = f"P{index + 1}"
    if mapping:
        return mapping

    # Legacy runs stored count only when hybrid ranking was disabled.
    count = event.payload.get("count")
    if isinstance(count, int) and count > 0:
        documents = get_run_source_documents(db, run_id)
        for index, doc in enumerate(documents[:count]):
            mapping[str(doc.id)] = f"P{index + 1}"
    return mapping


def _serialize_source_document(doc: SourceDocument, *, paper_id: str | None = None) -> dict:
    qualis = _qualis_fields_from_metadata(doc.metadata_)
    return SourceDocumentResponse(
        id=doc.id,
        source=doc.source,
        title=doc.title,
        abstract=doc.abstract,
        authors=doc.authors,
        year=doc.year,
        venue=doc.venue,
        doi=doc.doi,
        url=doc.url,
        citation_count=doc.citation_count or 0,
        qualis_estrato=qualis.get("qualis_estrato"),
    ).model_dump(mode="json") | ({"paper_id": paper_id} if paper_id else {})


def serialize_source_documents(
    documents: list[SourceDocument],
    *,
    paper_id_by_doc_id: dict[str, str] | None = None,
) -> list[dict]:
    return [
        _serialize_source_document(
            doc,
            paper_id=(paper_id_by_doc_id or {}).get(str(doc.id)),
        )
        for doc in documents
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


def _qualis_fields_from_metadata(metadata: dict | None) -> dict[str, str | float]:
    if not isinstance(metadata, dict):
        return {}

    fields: dict[str, str | float] = {}
    estrato = metadata.get("qualis_estrato")
    if isinstance(estrato, str) and estrato.strip():
        fields["qualis_estrato"] = estrato.strip().upper()

    boost = metadata.get("qualis_boost")
    if isinstance(boost, (int, float)):
        fields["qualis_boost"] = float(boost)

    period = metadata.get("qualis_period")
    if isinstance(period, str) and period.strip():
        fields["qualis_period"] = period.strip()

    return fields


def _relevance_score_from_metadata(metadata: dict | None) -> float | None:
    if not isinstance(metadata, dict):
        return None

    for key in ("llm_relevance_score", "relevance_score", "deterministic_relevance_score"):
        raw = metadata.get(key)
        if isinstance(raw, (int, float)):
            score = float(raw)
            if score > 1.0:
                score /= 100.0
            return max(0.0, min(1.0, score))
    return None


def enrich_evidence_papers(
    evidence_papers: list | None,
    documents: list[SourceDocument],
    *,
    paper_id_by_doc_id: dict[str, str] | None = None,
) -> list[dict]:
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

        paper_id = str(item.get("paper_id") or "").strip() or None
        if not paper_id and matched and paper_id_by_doc_id:
            paper_id = paper_id_by_doc_id.get(str(matched.id))

        entry = {
            "title": item.get("title"),
            "year": item.get("year"),
            "doi": item.get("doi"),
            "url": item.get("url"),
            "why_relevant": item.get("why_relevant"),
            "paper_id": paper_id,
            "authors": item.get("authors") or (matched.authors if matched else None),
            "retrieval_source": matched.source if matched else None,
            "citation_count": matched.citation_count if matched else None,
            "venue": matched.venue if matched else None,
            "abstract": matched.abstract if matched else None,
            "matched_in_catalog": matched is not None,
        }
        if matched and not entry["url"]:
            entry["url"] = matched.url
        if matched:
            entry.update(_qualis_fields_from_metadata(matched.metadata_))
            relevance = _relevance_score_from_metadata(matched.metadata_)
            if relevance is not None:
                entry["relevance_score"] = relevance
        enriched.append(entry)

    return enriched
