"""Academic paper retrieval from multiple open sources."""

import asyncio
import sys
from typing import Any

import httpx
from sqlalchemy.orm import Session

from apps.api.features.retrieval.cache import retrieval_cache_service
from apps.api.features.retrieval.corpus import corpus_retrieval_service
from apps.api.features.retrieval.fetch_queue import FetchJob, FetchQueueProcessor

# Re-export normalizers for backward-compatible imports in tests and deferred tasks.
from apps.api.features.retrieval.normalizers import (  # noqa: F401
    _content_hash,
    _normalize_crossref_work,
    _normalize_doi,
    _normalize_openalex_work,
    _normalize_semantic_scholar_paper,
    _reconstruct_abstract,
)
from apps.api.features.retrieval.persistence import persist_papers
from apps.api.features.retrieval.relevance import filter_and_rank_papers, filter_papers_by_max_age
from apps.api.features.retrieval.source_clients import AcademicSourceClient
from apps.api.shared.infra.resilience.registry import get_source_circuit_breaker
from apps.api.shared.models import SourceDocument
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.dual_pass import merge_dual_pass_results
from packages.postrec_core.retrieval.paper_enrichment import enrich_paper_metadata
from packages.postrec_core.retrieval.paper_tier import current_year
from packages.postrec_core.retrieval.retrieval_plan import build_retrieval_plan

logger = get_logger("postrec-retrieval")

SOURCE_FETCHERS = ("openalex", "arxiv", "semantic_scholar", "crossref")


class RetrievalService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._max_article_age_years = self.settings.retrieval_max_article_age_years

    def _article_age_cutoff(self) -> int:
        return current_year() - self._max_article_age_years

    def _source_client(self) -> AcademicSourceClient:
        return AcademicSourceClient(self.settings, self._article_age_cutoff())

    async def retrieve_papers(
        self,
        db: Session,
        topics: list[str],
        max_papers: int = 50,
        *,
        research_area: str | None = None,
        learned_topics: list[str] | None = None,
        avoided_topics: list[str] | None = None,
        max_article_age_years: int | None = None,
    ) -> list[SourceDocument]:
        self._max_article_age_years = max_article_age_years or self.settings.retrieval_max_article_age_years
        cleaned_topics = [t.strip() for t in topics if t and t.strip()]
        if not cleaned_topics:
            return []

        fetch_target = min(max(max_papers * 2, max_papers + 20), 200)
        raw_papers: list[dict[str, Any]] = []

        if self.settings.retrieval_corpus_prefetch_enabled:
            raw_papers.extend(
                corpus_retrieval_service.prefetch_papers(
                    db,
                    topics=cleaned_topics,
                    research_area=research_area,
                    learned_topics=learned_topics,
                    min_score=max(self.settings.retrieval_min_relevance_score, 0.28),
                    max_papers=min(fetch_target, max_papers + 10),
                )
            )

        jobs = self._build_fetch_jobs(
            cleaned_topics,
            fetch_target,
            research_area=research_area,
            learned_topics=learned_topics,
        )
        jobs.sort(key=lambda job: (job.priority, job.source, job.query, job.job_type))

        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            processor = FetchQueueProcessor(
                lambda job: self._dispatch_job(client, job),
                max_attempts=self.settings.retrieval_fetch_max_attempts,
                circuit_breaker=get_source_circuit_breaker(),
                min_unique_papers=self.settings.retrieval_min_papers_before_skip,
            )
            queue_result = await processor.process(jobs)
            raw_papers.extend(queue_result.papers)

            if queue_result.exhausted_jobs:
                deferred = await self._retry_exhausted_fetches(client, queue_result.exhausted_jobs)
                raw_papers.extend(deferred)
                logger.info(
                    "deferred_fetch_complete",
                    requested=len(queue_result.exhausted_jobs),
                    recovered=len(deferred),
                )

            recommendation_papers = await self._fetch_semantic_scholar_recommendations(
                client,
                raw_papers,
                fetch_target,
            )
            raw_papers.extend(recommendation_papers)

        if self.settings.dual_retrieval_enabled:
            sota_papers = [p for p in raw_papers if p.get("retrieval_pass") == "sota"]
            foundation_papers = [
                p for p in raw_papers if p.get("retrieval_pass") in ("foundation", "corpus", "recommendations")
            ]
            papers = merge_dual_pass_results(
                sota_papers,
                foundation_papers,
                max_papers=fetch_target,
                sota_quota=self.settings.sota_tier_quota,
                recent_years=self.settings.sota_recent_years,
                seminal_citation_threshold=self.settings.sota_seminal_citation_threshold,
            )
        else:
            papers = raw_papers

        papers = [enrich_paper_metadata(paper) for paper in papers if isinstance(paper, dict)]

        papers, age_stats = filter_papers_by_max_age(
            papers,
            max_age_years=self._max_article_age_years,
        )

        papers, filter_stats = filter_and_rank_papers(
            papers,
            topics=cleaned_topics,
            research_area=research_area,
            learned_topics=learned_topics,
            avoided_topics=avoided_topics,
            min_score=self.settings.retrieval_min_relevance_score,
            max_papers=fetch_target,
        )
        saved = persist_papers(db, papers, max_papers)

        logger.info(
            "papers_retrieved",
            count=len(saved),
            requested=max_papers,
            sources_collected=len(papers),
            fetch_jobs=len(jobs),
            corpus_prefetched=bool(self.settings.retrieval_corpus_prefetch_enabled),
            recommendations_added=len(recommendation_papers),
            fetch_requeued=queue_result.requeued_jobs,
            fetch_exhausted=len(queue_result.exhausted_jobs),
            fetch_skipped_circuit=queue_result.skipped_circuit_jobs,
            fetch_early_stopped=queue_result.early_stopped,
            relevance_input=filter_stats["input"],
            relevance_filtered_out=filter_stats["filtered_out"],
            relevance_kept=filter_stats["kept"],
            age_filtered_out=age_stats["filtered_out"],
            max_article_age_years=self._max_article_age_years,
        )
        return saved

    async def fetch_source(
        self, source: str, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            job = FetchJob(source=source, query=query, limit=limit, pass_kind=pass_kind)
            return await self._dispatch_job(client, job)

    def _source_priority_map(self) -> dict[str, int]:
        order = [part.strip() for part in self.settings.retrieval_source_priority.split(",") if part.strip()]
        return {source: index for index, source in enumerate(order)}

    def _build_fetch_jobs(
        self,
        topics: list[str],
        fetch_target: int,
        *,
        research_area: str | None,
        learned_topics: list[str] | None,
    ) -> list[FetchJob]:
        return self._build_jobs_from_plan(
            topics,
            fetch_target,
            research_area=research_area,
            learned_topics=learned_topics,
        )

    def _primary_source_limit(self, fetch_target: int) -> int:
        return min(
            self.settings.retrieval_openalex_per_page_max,
            max(30, fetch_target // 2),
        )

    def _crossref_limit(self, fetch_target: int) -> int:
        return min(
            self.settings.retrieval_crossref_rows_max,
            max(20, fetch_target // 3),
        )

    def _semantic_scholar_limit(self, fetch_target: int) -> int:
        return min(
            self.settings.retrieval_semantic_scholar_limit_max,
            max(25, fetch_target // 2),
        )

    def _build_jobs_from_plan(
        self,
        topics: list[str],
        fetch_target: int,
        *,
        research_area: str | None,
        learned_topics: list[str] | None,
    ) -> list[FetchJob]:
        plan = build_retrieval_plan(
            topics,
            research_area=research_area,
            learned_topics=learned_topics,
            include_sota_terms=True,
            learned_topic_cap=self.settings.retrieval_learned_topic_cap,
            dual_pass=self.settings.dual_retrieval_enabled,
        )
        priority_map = self._source_priority_map()
        jobs: list[FetchJob] = []
        crossref_slots = self.settings.retrieval_crossref_max_queries
        primary_limit = self._primary_source_limit(fetch_target)
        crossref_limit = self._crossref_limit(fetch_target)
        s2_limit = self._semantic_scholar_limit(fetch_target)

        for search in plan.searches:
            for pass_kind in search.pass_kinds:
                jobs.append(
                    FetchJob(
                        source="openalex",
                        query=search.query,
                        limit=primary_limit,
                        pass_kind=pass_kind,
                        priority=priority_map.get("openalex", 99),
                    )
                )
                jobs.append(
                    FetchJob(
                        source="semantic_scholar",
                        query=search.query,
                        limit=s2_limit,
                        pass_kind=pass_kind,
                        priority=priority_map.get("semantic_scholar", 99),
                    )
                )
                if search.use_crossref and crossref_slots > 0:
                    jobs.append(
                        FetchJob(
                            source="crossref",
                            query=search.query,
                            limit=crossref_limit,
                            pass_kind=pass_kind,
                            priority=priority_map.get("crossref", 99),
                        )
                    )
                    crossref_slots -= 1

        for learned in plan.learned_queries:
            jobs.append(
                FetchJob(
                    source="openalex",
                    query=learned,
                    limit=primary_limit,
                    pass_kind="foundation",
                    priority=priority_map.get("openalex", 99),
                )
            )
            jobs.append(
                FetchJob(
                    source="semantic_scholar",
                    query=learned,
                    limit=s2_limit,
                    pass_kind="foundation",
                    priority=priority_map.get("semantic_scholar", 99),
                )
            )

        if plan.arxiv_query:
            jobs.append(
                FetchJob(
                    source="arxiv",
                    query=plan.arxiv_query,
                    limit=min(self.settings.retrieval_arxiv_max_results, primary_limit),
                    pass_kind="sota",
                    priority=priority_map.get("arxiv", 99),
                )
            )

        return jobs

    async def _dispatch_job(self, client: httpx.AsyncClient, job: FetchJob) -> list[dict[str, Any]]:
        cached = retrieval_cache_service.get(
            job.source,
            job.query,
            job.limit,
            job.pass_kind,
            job.job_type,
        )
        if cached is not None:
            for paper in cached:
                paper["retrieval_pass"] = job.pass_kind
            return cached

        sources = self._source_client()
        if job.job_type == "recommendations":
            papers = await sources.fetch_semantic_scholar_recommendations_for_seeds(
                client,
                list(job.seed_paper_ids),
                job.limit,
            )
        elif job.source == "openalex":
            papers = await sources.fetch_openalex(client, job.query, job.limit, job.pass_kind)
        elif job.source == "arxiv":
            papers = await sources.fetch_arxiv(client, job.query, job.limit, job.pass_kind)
        elif job.source == "semantic_scholar":
            papers = await sources.fetch_semantic_scholar(client, job.query, job.limit, job.pass_kind)
        elif job.source == "crossref":
            papers = await sources.fetch_crossref(client, job.query, job.limit, job.pass_kind)
        else:
            raise ValueError(f"Unknown source: {job.source}")

        for paper in papers:
            paper["retrieval_pass"] = job.pass_kind
        if papers:
            retrieval_cache_service.set(
                job.source,
                job.query,
                job.limit,
                job.pass_kind,
                papers,
                job.job_type,
            )
        return papers

    def _semantic_scholar_seed_ids(self, papers: list[dict[str, Any]]) -> list[str]:
        ranked = sorted(
            papers,
            key=lambda paper: (
                paper.get("relevance_score") or 0.0,
                paper.get("citation_count") or 0,
            ),
            reverse=True,
        )
        seeds: list[str] = []
        seen: set[str] = set()
        for paper in ranked:
            if paper.get("source") != "semantic_scholar":
                continue
            paper_id = str(paper.get("external_id") or "").strip()
            if not paper_id or paper_id in seen:
                continue
            seen.add(paper_id)
            seeds.append(paper_id)
            if len(seeds) >= self.settings.retrieval_s2_recommendation_seeds:
                break
        return seeds

    async def _fetch_semantic_scholar_recommendations(
        self,
        client: httpx.AsyncClient,
        papers: list[dict[str, Any]],
        fetch_target: int,
    ) -> list[dict[str, Any]]:
        if not self.settings.retrieval_s2_recommendations_enabled:
            return []

        seeds = self._semantic_scholar_seed_ids(papers)
        if len(seeds) < 2:
            return []

        limit = min(
            self.settings.retrieval_s2_recommendation_limit,
            max(20, fetch_target),
        )
        job = FetchJob(
            source="semantic_scholar",
            query="|".join(seeds),
            limit=limit,
            pass_kind="foundation",
            job_type="recommendations",
            seed_paper_ids=tuple(seeds),
            priority=10,
        )
        try:
            from apps.api.shared.infra.source_rate_limiter import source_rate_limiter

            await source_rate_limiter.wait_async("semantic_scholar")
            return await self._dispatch_job(client, job)
        except Exception as exc:
            logger.warning(
                "semantic_scholar_recommendations_failed",
                seeds=len(seeds),
                error=f"{type(exc).__name__}: {exc}",
            )
            return []

    async def _retry_exhausted_fetches(
        self, client: httpx.AsyncClient, exhausted_jobs: list[FetchJob]
    ) -> list[dict[str, Any]]:
        """Second-chance fetches with longer spacing; uses Celery queue when workers are available."""
        if sys.platform == "win32":
            return await self._retry_exhausted_inline(client, exhausted_jobs)

        if self.settings.retrieval_use_celery_deferred:
            return await self._dispatch_celery_retries(exhausted_jobs)

        return await self._retry_exhausted_inline(client, exhausted_jobs)

    async def _retry_exhausted_inline(
        self, client: httpx.AsyncClient, exhausted_jobs: list[FetchJob]
    ) -> list[dict[str, Any]]:
        from apps.api.shared.infra.source_rate_limiter import source_rate_limiter

        papers: list[dict[str, Any]] = []
        for index, job in enumerate(exhausted_jobs):
            delay = min(15 * (index + 1), 60)
            logger.info(
                "inline_deferred_fetch_scheduled",
                source=job.source,
                query=job.query,
                delay_seconds=delay,
            )
            await asyncio.sleep(delay)
            await source_rate_limiter.wait_async(job.source)
            try:
                batch = await self._dispatch_job(client, job)
                papers.extend(batch)
                logger.info(
                    "inline_deferred_fetch_ok",
                    source=job.source,
                    query=job.query,
                    count=len(batch),
                )
            except Exception as exc:
                logger.warning(
                    "inline_deferred_fetch_failed",
                    source=job.source,
                    query=job.query,
                    error=f"{type(exc).__name__}: {exc}",
                )
        return papers

    async def _dispatch_celery_retries(self, exhausted_jobs: list[FetchJob]) -> list[dict[str, Any]]:
        if not exhausted_jobs or not self.settings.retrieval_use_celery_deferred:
            return []

        from apps.api.workers.tasks import deferred_source_fetch

        papers: list[dict[str, Any]] = []
        async_results = []
        for index, job in enumerate(exhausted_jobs):
            countdown = min(15 * (index + 1), 90)
            async_results.append(
                deferred_source_fetch.apply_async(
                    args=[job.source, job.query, job.limit, job.pass_kind],
                    queue="postrec.recommendation.retrieval",
                    countdown=countdown,
                )
            )
            logger.info(
                "celery_deferred_fetch_scheduled",
                source=job.source,
                query=job.query,
                countdown=countdown,
            )

        for async_result in async_results:
            try:
                batch = async_result.get(timeout=self.settings.retrieval_deferred_timeout_seconds)
                if batch:
                    papers.extend(batch)
            except Exception as exc:
                logger.warning("celery_deferred_fetch_failed", error=f"{type(exc).__name__}: {exc}")

        return papers


retrieval_service = RetrievalService()
