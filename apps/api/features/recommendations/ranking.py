"""Hybrid retrieval orchestration (embeddings + tier quotas)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from apps.api.features.qualis.service import qualis_service
from apps.api.features.recommendations.llm import gemini_service
from apps.api.features.retrieval.relevance import compute_relevance_score
from apps.api.features.retrieval.vector import vector_retrieval_service
from apps.api.shared.models import SourceDocument
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.bm25 import Bm25Index, bm25_score_paper
from packages.postrec_core.retrieval.hybrid_ranking import rank_papers_by_hybrid_score
from packages.postrec_core.retrieval.paper_tier import tag_paper_tiers
from packages.postrec_core.retrieval.tier_quota import apply_tier_quotas

logger = get_logger("postrec-hybrid-retrieval")


class HybridRankingService:
    """Re-rank persisted papers using BM25, dense embeddings, pgvector, and SOTA tier quotas."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def build_query_text(
        self,
        *,
        topics: list[str],
        research_area: str | None,
        expected_output: str | None = None,
    ) -> str:
        parts = list(topics)
        if research_area:
            parts.append(research_area)
        if expected_output:
            parts.append(expected_output)
        return ". ".join(p.strip() for p in parts if p and p.strip())

    def build_ranking_event_payload(self, selected: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "papers": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "tier": item.get("tier"),
                    "hybrid_score": item.get("hybrid_score"),
                    "dense_score": item.get("dense_score"),
                    "relevance_score": item.get("relevance_score"),
                    "retrieval_pass": item.get("retrieval_pass"),
                }
                for item in selected
            ],
            "count": len(selected),
        }

    def _documents_to_ranking_items(self, documents: list[SourceDocument]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for doc in documents:
            metadata = doc.metadata_ or {}
            items.append(
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "tier": metadata.get("tier"),
                    "hybrid_score": metadata.get("hybrid_score"),
                    "dense_score": metadata.get("dense_score"),
                    "relevance_score": metadata.get("relevance_score"),
                    "retrieval_pass": metadata.get("retrieval_pass"),
                }
            )
        return items

    def rerank_papers(
        self,
        db: Session,
        run_id: str,
        papers: list[SourceDocument],
        paper_embeddings: list[list[float]],
        *,
        topics: list[str],
        research_area: str | None,
        expected_output: str | None,
        max_papers: int,
    ) -> tuple[list[SourceDocument], dict[str, Any]]:
        if not papers:
            return [], {"papers": [], "count": 0}

        settings = self._settings
        if not settings.hybrid_retrieval_enabled or len(papers) != len(paper_embeddings):
            selected = papers[:max_papers]
            return selected, self.build_ranking_event_payload(self._documents_to_ranking_items(selected))

        query_text = self.build_query_text(
            topics=topics,
            research_area=research_area,
            expected_output=expected_output,
        )

        corpus_docs = [f"{paper.title}. {paper.abstract or ''}" for paper in papers]
        bm25_index = Bm25Index.from_documents(corpus_docs) if settings.bm25_sparse_enabled else None
        paper_dicts: list[dict[str, Any]] = []
        for paper in papers:
            metadata = paper.metadata_ or {}
            paper_payload = {
                "title": paper.title,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "citation_count": paper.citation_count,
                "issn": metadata.get("issn"),
                "journal_title": metadata.get("journal_title") or paper.venue,
                "metadata": metadata,
            }
            if settings.bm25_sparse_enabled and bm25_index is not None:
                sparse_score = bm25_score_paper(
                    query_text,
                    paper_payload,
                    index=bm25_index,
                )
            else:
                sparse_score = compute_relevance_score(
                    paper_payload,
                    topics=topics,
                    research_area=research_area,
                )

            if settings.bm25_sparse_enabled and bm25_index is not None:
                sparse_score, qualis_meta = qualis_service.apply_relevance_boost(sparse_score, paper_payload)
            else:
                # compute_relevance_score already applied the boost; capture metadata only.
                qualis_meta = {}
                boost, estrato, period = qualis_service.boost_for_paper(paper_payload)
                if boost > 0.0 or estrato is not None:
                    qualis_meta = {
                        "qualis_estrato": estrato,
                        "qualis_boost": boost,
                    }
                    if period:
                        qualis_meta["qualis_period"] = period

            paper_dicts.append(
                {
                    "id": str(paper.id),
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "venue": paper.venue,
                    "year": paper.year,
                    "citation_count": paper.citation_count or 0,
                    "relevance_score": sparse_score,
                    "retrieval_pass": metadata.get("retrieval_pass"),
                    "methods": metadata.get("methods"),
                    "limitations": metadata.get("limitations"),
                    **qualis_meta,
                }
            )

        query_embedding = gemini_service.generate_embeddings(db, run_id, [query_text])[0]

        if settings.vector_retrieval_enabled:
            candidate_ids = [paper.id for paper in papers]
            vector_scores = vector_retrieval_service.find_similar_document_ids(
                db,
                query_embedding,
                candidate_ids=candidate_ids,
                limit=settings.vector_retrieval_top_k,
            )
            for paper_dict in paper_dicts:
                vector_score = vector_scores.get(paper_dict["id"], 0.0)
                paper_dict["relevance_score"] = round(
                    0.75 * float(paper_dict["relevance_score"]) + 0.25 * vector_score,
                    4,
                )

        ranked = rank_papers_by_hybrid_score(
            paper_dicts,
            paper_embeddings,
            query_embedding,
            sparse_weight=settings.hybrid_sparse_weight,
        )
        tagged = tag_paper_tiers(
            ranked,
            recent_years=settings.sota_recent_years,
            seminal_citation_threshold=settings.sota_seminal_citation_threshold,
        )
        selected = apply_tier_quotas(
            tagged,
            max_papers,
            sota_quota=settings.sota_tier_quota,
        )

        by_id = {str(p.id): p for p in papers}
        ordered: list[SourceDocument] = []
        for item in selected:
            doc = by_id.get(item["id"])
            if not doc:
                continue
            metadata = dict(doc.metadata_ or {})
            metadata.update(
                {
                    "tier": item.get("tier"),
                    "hybrid_score": item.get("hybrid_score"),
                    "dense_score": item.get("dense_score"),
                    "relevance_score": item.get("relevance_score"),
                }
            )
            if item.get("qualis_estrato"):
                metadata["qualis_estrato"] = item.get("qualis_estrato")
            if item.get("qualis_boost"):
                metadata["qualis_boost"] = item.get("qualis_boost")
            if item.get("qualis_period"):
                metadata["qualis_period"] = item.get("qualis_period")
            doc.metadata_ = metadata
            ordered.append(doc)

        event_payload = self.build_ranking_event_payload(selected)
        logger.info(
            "hybrid_rerank_complete",
            input_count=len(papers),
            output_count=len(ordered),
            sota_recent=sum(1 for p in selected if p.get("tier") == "sota_recent"),
        )
        return ordered, event_payload


hybrid_ranking_service = HybridRankingService()
