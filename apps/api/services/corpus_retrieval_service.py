"""Load relevant papers already stored locally before calling external APIs."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from apps.api.models import SourceDocument
from apps.api.observability.logging import get_logger
from apps.api.services.relevance_service import compute_relevance_score, tokenize

logger = get_logger("postrec-corpus-retrieval")


class CorpusRetrievalService:
    """Lexical prefetch from ``source_document`` — no paid API calls."""

    def prefetch_papers(
        self,
        db: Session,
        *,
        topics: list[str],
        research_area: str | None = None,
        learned_topics: list[str] | None = None,
        min_score: float = 0.28,
        max_papers: int = 40,
        candidate_pool: int = 400,
    ) -> list[dict]:
        tokens: set[str] = set()
        for phrase in topics:
            tokens.update(tokenize(phrase))
        if research_area:
            tokens.update(tokenize(research_area))
        for phrase in learned_topics or []:
            tokens.update(tokenize(phrase))

        significant = sorted(token for token in tokens if len(token) > 3)[:8]
        if not significant:
            return []

        clauses = []
        for token in significant:
            pattern = f"%{token}%"
            clauses.append(SourceDocument.title.ilike(pattern))
            clauses.append(SourceDocument.abstract.ilike(pattern))

        candidates = (
            db.query(SourceDocument)
            .filter(or_(*clauses))
            .order_by(SourceDocument.citation_count.desc())
            .limit(candidate_pool)
            .all()
        )

        scored: list[tuple[float, dict]] = []
        for doc in candidates:
            paper = self._document_to_paper(doc)
            score = compute_relevance_score(
                paper,
                topics=topics,
                research_area=research_area,
                learned_topics=learned_topics,
            )
            if score >= min_score:
                paper["relevance_score"] = round(score, 4)
                paper["retrieval_pass"] = "corpus"
                scored.append((score, paper))

        scored.sort(key=lambda item: (item[0], item[1].get("citation_count") or 0), reverse=True)
        papers = [paper for _, paper in scored[:max_papers]]

        logger.info(
            "corpus_prefetch_complete",
            tokens=len(significant),
            candidates=len(candidates),
            kept=len(papers),
        )
        return papers

    @staticmethod
    def _document_to_paper(doc: SourceDocument) -> dict:
        metadata = dict(doc.metadata_ or {})
        return {
            "external_id": doc.external_id,
            "source": doc.source,
            "title": doc.title,
            "abstract": doc.abstract,
            "authors": doc.authors,
            "year": doc.year,
            "venue": doc.venue,
            "doi": doc.doi,
            "url": doc.url,
            "citation_count": doc.citation_count or 0,
            "metadata": metadata,
            "_corpus_document_id": str(doc.id),
        }


corpus_retrieval_service = CorpusRetrievalService()
