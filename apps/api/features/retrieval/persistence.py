"""Persist retrieved paper dicts as SourceDocument rows."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from apps.api.features.retrieval.normalizers import content_hash, normalize_doi
from apps.api.shared.models import SourceDocument

VALIDATION_METADATA_KEYS = (
    "article_validation_method",
    "llm_relevance_score",
    "deterministic_relevance_score",
    "llm_passes_validation",
    "llm_matched_topics",
    "llm_match_rationale",
    "llm_avoided_topic_hit",
    "article_validated_at_run_id",
)


def merge_paper_metadata(doc: SourceDocument, paper: dict[str, Any]) -> None:
    metadata = dict(doc.metadata_ or {})
    incoming = paper.get("metadata") if isinstance(paper.get("metadata"), dict) else {}
    for key in ("tier", "retrieval_pass", "methods", "limitations", "hybrid_score", "dense_score"):
        value = paper.get(key)
        if value is None:
            value = incoming.get(key)
        if value is not None:
            metadata[key] = value
    doc.metadata_ = metadata


def merge_validation_metadata(
    doc: SourceDocument,
    paper: dict[str, Any],
    *,
    run_id: str,
    method: str,
) -> None:
    metadata = dict(doc.metadata_ or {})
    metadata["article_validation_method"] = method
    metadata["article_validated_at_run_id"] = run_id

    llm_score = paper.get("llm_relevance_score")
    if llm_score is not None:
        metadata["llm_relevance_score"] = llm_score
    det_score = paper.get("relevance_score")
    if det_score is not None:
        metadata["deterministic_relevance_score"] = det_score
    if "llm_passes_validation" in paper:
        metadata["llm_passes_validation"] = bool(paper["llm_passes_validation"])
    for key in ("llm_matched_topics", "llm_match_rationale", "llm_avoided_topic_hit"):
        if key in paper and paper[key] is not None:
            metadata[key] = paper[key]

    doc.metadata_ = metadata


def persist_article_validation_scores(
    db: Session,
    papers: list[dict[str, Any]],
    *,
    run_id: str,
    method: str,
) -> int:
    """Write article-validation scores onto linked SourceDocument rows."""
    doc_ids: list[uuid.UUID] = []
    paper_by_doc_id: dict[uuid.UUID, dict[str, Any]] = {}
    for paper in papers:
        raw_id = paper.get("source_document_id")
        if not raw_id:
            continue
        try:
            doc_id = uuid.UUID(str(raw_id))
        except (TypeError, ValueError):
            continue
        doc_ids.append(doc_id)
        paper_by_doc_id[doc_id] = paper

    if not doc_ids:
        return 0

    updated = 0
    for doc in db.query(SourceDocument).filter(SourceDocument.id.in_(doc_ids)).all():
        paper = paper_by_doc_id.get(doc.id)
        if not paper:
            continue
        merge_validation_metadata(doc, paper, run_id=run_id, method=method)
        updated += 1

    if updated:
        db.commit()
    return updated


def persist_papers(db: Session, papers: list[dict[str, Any]], max_papers: int) -> list[SourceDocument]:
    seen_hashes: set[str] = set()
    seen_dois: set[str] = set()
    saved: list[SourceDocument] = []
    pending: list[tuple[str | None, str, dict[str, Any]]] = []

    for paper in papers:
        if len(saved) + len(pending) >= max_papers:
            break
        if not isinstance(paper, dict) or not paper.get("title") or not paper.get("source"):
            continue

        doi = normalize_doi(paper.get("doi"))
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)

        paper_hash = content_hash(paper["title"], paper.get("abstract"))
        if paper_hash in seen_hashes:
            continue
        seen_hashes.add(paper_hash)
        pending.append((doi, paper_hash, paper))

    dois = [doi for doi, _, _ in pending if doi]
    hashes = [paper_hash for _, paper_hash, _ in pending]
    existing_by_doi: dict[str, SourceDocument] = {}
    existing_by_hash: dict[str, SourceDocument] = {}
    if dois:
        for doc in db.query(SourceDocument).filter(SourceDocument.doi.in_(dois)).all():
            if doc.doi:
                existing_by_doi[str(doc.doi)] = doc
    if hashes:
        for doc in db.query(SourceDocument).filter(SourceDocument.content_hash.in_(hashes)).all():
            if doc.content_hash:
                existing_by_hash[str(doc.content_hash)] = doc

    for doi, paper_hash, paper in pending:
        if len(saved) >= max_papers:
            break
        existing = existing_by_doi.get(doi) if doi else None
        if existing is None:
            existing = existing_by_hash.get(paper_hash)
        if existing:
            merge_paper_metadata(existing, paper)
            saved.append(existing)
            continue

        doc = SourceDocument(
            external_id=paper.get("external_id"),
            source=paper["source"],
            title=paper["title"],
            abstract=paper.get("abstract"),
            authors=paper.get("authors"),
            year=paper.get("year"),
            venue=paper.get("venue"),
            doi=doi,
            url=paper.get("url"),
            citation_count=paper.get("citation_count", 0),
            content_hash=paper_hash,
            metadata_=paper.get("metadata") or {},
        )
        db.add(doc)
        saved.append(doc)

    db.commit()
    return saved
