"""OpenAlex academic paper retrieval."""

import asyncio
import sys
from collections.abc import Callable
from typing import Any

import httpx
from sqlalchemy.orm import Session

from apps.api.features.retrieval.cache import retrieval_cache_service
from apps.api.features.retrieval.corpus import corpus_retrieval_service
from apps.api.features.retrieval.fetch_queue import FetchJob, FetchQueueProcessor
from apps.api.features.retrieval.persistence import persist_papers
from apps.api.features.retrieval.relevance import filter_and_rank_papers, filter_papers_by_max_age
from apps.api.features.retrieval.source_clients import OpenAlexClient
from apps.api.features.retrieval.taxonomy_bootstrap import ensure_openalex_taxonomy_cache
from apps.api.shared.infra.resilience.registry import get_source_circuit_breaker
from apps.api.shared.models import SourceDocument
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.dual_pass import merge_dual_pass_results
from packages.postrec_core.retrieval.openalex_metrics import OpenAlexRunMetrics, summarize_alignment_stats
from packages.postrec_core.retrieval.openalex_query import extract_openalex_work_id
from packages.postrec_core.retrieval.paper_enrichment import enrich_paper_metadata
from packages.postrec_core.retrieval.paper_tier import current_year
from packages.postrec_core.retrieval.retrieval_plan import build_retrieval_plan

logger = get_logger("postrec-retrieval")


class RetrievalService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._max_article_age_years = self.settings.retrieval_max_article_age_years

    def _article_age_cutoff(self) -> int:
        return current_year() - self._max_article_age_years

    def _openalex_client(self, metrics: OpenAlexRunMetrics | None = None) -> OpenAlexClient:
        return OpenAlexClient(self.settings, self._article_age_cutoff(), metrics=metrics)

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
        on_milestone: Callable[[str, int], None] | None = None,
    ) -> list[SourceDocument]:
        self._max_article_age_years = max_article_age_years or self.settings.retrieval_max_article_age_years
        cleaned_topics = [t.strip() for t in topics if t and t.strip()]
        if not cleaned_topics:
            return []

        ensure_openalex_taxonomy_cache()
        openalex_metrics = OpenAlexRunMetrics()
        fetch_target = min(max(max_papers * 2, max_papers + 20), 200)
        raw_papers: list[dict[str, Any]] = []

        if self.settings.retrieval_corpus_prefetch_enabled:
            raw_papers.extend(
                corpus_retrieval_service.prefetch_papers(
                    db,
                    topics=cleaned_topics,
                    research_area=research_area,
                    learned_topics=learned_topics,
                    min_score=max(
                        self.settings.retrieval_min_relevance_score,
                        self.settings.retrieval_corpus_prefetch_min_score,
                    ),
                    max_papers=min(fetch_target, max_papers + 10),
                )
            )

        jobs = self._build_fetch_jobs(
            cleaned_topics,
            fetch_target,
            research_area=research_area,
            learned_topics=learned_topics,
        )
        jobs.sort(key=lambda job: (job.priority, job.source, job.query, job.pass_kind))

        if on_milestone:
            on_milestone("Querying OpenAlex for relevant papers…", 18)

        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            openalex_client = self._openalex_client(openalex_metrics)
            if self.settings.retrieval_openalex_log_rate_limit and self.settings.openalex_api_key:
                rate_limit = await openalex_client.fetch_rate_limit(client)
                if rate_limit:
                    logger.info("openalex_rate_limit_status", **self._summarize_rate_limit(rate_limit))

            processor = FetchQueueProcessor(
                lambda job: self._dispatch_job(client, job, metrics=openalex_metrics),
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

            raw_papers = await self._expand_openalex_citation_graph(
                client,
                raw_papers,
                research_area=research_area,
                topics=cleaned_topics,
                metrics=openalex_metrics,
            )
            raw_papers = await self._enrich_papers_via_openalex_doi(
                client,
                raw_papers,
                metrics=openalex_metrics,
            )

        if on_milestone:
            on_milestone(f"Collected {len(raw_papers)} papers from sources", 24)

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

        if on_milestone:
            on_milestone("Scoring papers for relevance to your topics", 28)

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

        alignment_summary = summarize_alignment_stats(papers)
        logger.info(
            "papers_retrieved",
            count=len(saved),
            requested=max_papers,
            sources_collected=len(papers),
            fetch_jobs=len(jobs),
            corpus_prefetched=bool(self.settings.retrieval_corpus_prefetch_enabled),
            recommendations_added=0,
            fetch_requeued=queue_result.requeued_jobs,
            fetch_exhausted=len(queue_result.exhausted_jobs),
            fetch_skipped_circuit=queue_result.skipped_circuit_jobs,
            fetch_early_stopped=queue_result.early_stopped,
            relevance_input=filter_stats["input"],
            relevance_filtered_out=filter_stats["filtered_out"],
            relevance_kept=filter_stats["kept"],
            alignment_rejected=filter_stats.get("alignment_rejected", 0),
            keyword_traps_seen=filter_stats.get("keyword_traps_seen", 0),
            wrong_field_rate=alignment_summary["wrong_field_rate"],
            keyword_trap_rate=alignment_summary["keyword_trap_rate"],
            openalex_requests=openalex_metrics.summary(),
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
        jobs: list[FetchJob] = []
        primary_limit = self._primary_source_limit(fetch_target)
        topic_tuple = tuple(topics)
        openalex_tier = self.settings.retrieval_openalex_filter_tier
        use_search = self.settings.retrieval_openalex_use_search

        for search in plan.searches:
            for pass_kind in search.pass_kinds:
                jobs.append(
                    FetchJob(
                        source="openalex",
                        query=search.query,
                        limit=primary_limit,
                        pass_kind=pass_kind,
                        priority=0,
                        research_area=research_area,
                        topics=topic_tuple,
                        openalex_tier=openalex_tier,
                        use_search=use_search,
                    )
                )

        for learned in plan.learned_queries:
            jobs.append(
                FetchJob(
                    source="openalex",
                    query=learned,
                    limit=primary_limit,
                    pass_kind="foundation",
                    priority=0,
                    research_area=research_area,
                    topics=topic_tuple,
                    openalex_tier=openalex_tier,
                    use_search=use_search,
                )
            )

        return jobs

    async def _dispatch_job(
        self,
        client: httpx.AsyncClient,
        job: FetchJob,
        *,
        metrics: OpenAlexRunMetrics | None = None,
    ) -> list[dict[str, Any]]:
        cache_job_type = f"search:{job.openalex_tier}:{'q' if job.use_search else 'f'}"
        cached = retrieval_cache_service.get(
            job.source,
            job.query,
            job.limit,
            job.pass_kind,
            cache_job_type,
        )
        if cached is not None:
            for paper in cached:
                paper["retrieval_pass"] = job.pass_kind
            return cached

        if job.source != "openalex":
            raise ValueError(f"Unsupported retrieval source: {job.source}")

        openalex = self._openalex_client(metrics)
        papers = await openalex.fetch_works(
            client,
            job.query,
            job.limit,
            job.pass_kind,
            research_area=job.research_area,
            topics=list(job.topics),
            tier=job.openalex_tier,
            use_search=job.use_search,
        )

        for paper in papers:
            paper["retrieval_pass"] = job.pass_kind
        if papers:
            retrieval_cache_service.set(
                job.source,
                job.query,
                job.limit,
                job.pass_kind,
                papers,
                cache_job_type,
            )
        return papers

    @staticmethod
    def _summarize_rate_limit(payload: dict[str, Any]) -> dict[str, Any]:
        rate_limit = payload.get("rate_limit") if isinstance(payload.get("rate_limit"), dict) else {}
        return {
            "daily_budget_usd": rate_limit.get("daily_budget_usd"),
            "daily_used_usd": rate_limit.get("daily_used_usd"),
            "daily_remaining_usd": rate_limit.get("daily_remaining_usd"),
        }

    def _unique_paper_count(self, papers: list[dict[str, Any]]) -> int:
        keys = set()
        for paper in papers:
            key = paper.get("doi") or paper.get("external_id") or paper.get("title")
            if key:
                keys.add(str(key).lower())
        return len(keys)

    async def _enrich_papers_via_openalex_doi(
        self,
        client: httpx.AsyncClient,
        papers: list[dict[str, Any]],
        *,
        metrics: OpenAlexRunMetrics | None = None,
    ) -> list[dict[str, Any]]:
        if not self.settings.retrieval_openalex_doi_enrichment_enabled:
            return papers

        missing_abstract = [
            paper for paper in papers if isinstance(paper, dict) and paper.get("doi") and not paper.get("abstract")
        ]
        if not missing_abstract:
            return papers

        dois = [str(paper["doi"]) for paper in missing_abstract if paper.get("doi")]
        if not dois:
            return papers

        openalex = self._openalex_client(metrics)
        try:
            enriched_batch = await openalex.fetch_by_dois(
                client,
                dois,
                limit=len(dois),
            )
        except Exception as exc:
            logger.warning(
                "openalex_doi_enrichment_failed",
                dois=len(dois),
                error=f"{type(exc).__name__}: {exc}",
            )
            return papers

        by_doi = {str(paper.get("doi")).lower(): paper for paper in enriched_batch if paper.get("doi")}
        if not by_doi:
            return papers

        merged: list[dict[str, Any]] = []
        enriched_count = 0
        for paper in papers:
            doi = str(paper.get("doi") or "").lower()
            enrichment = by_doi.get(doi)
            if enrichment:
                updated = {**paper}
                for key in (
                    "abstract",
                    "openalex_primary_topic",
                    "openalex_field",
                    "openalex_subfield",
                    "openalex_topics",
                    "openalex_fwci",
                    "is_open_access",
                    "open_access_status",
                    "openalex_keywords",
                    "citation_count",
                    "external_id",
                ):
                    if not updated.get(key) and enrichment.get(key) is not None:
                        updated[key] = enrichment[key]
                if updated.get("abstract") and not paper.get("abstract"):
                    enriched_count += 1
                merged.append(updated)
            else:
                merged.append(paper)

        if enriched_count:
            logger.info("openalex_doi_enrichment", requested=len(dois), enriched=enriched_count)
        return merged

    async def _expand_openalex_citation_graph(
        self,
        client: httpx.AsyncClient,
        papers: list[dict[str, Any]],
        *,
        research_area: str | None,
        topics: list[str],
        metrics: OpenAlexRunMetrics | None = None,
    ) -> list[dict[str, Any]]:
        if not self.settings.retrieval_openalex_citation_expansion_enabled:
            return papers

        threshold = self.settings.retrieval_openalex_fallback_min_results
        if self._unique_paper_count(papers) >= threshold:
            return papers

        openalex_papers = [paper for paper in papers if paper.get("source") == "openalex" and paper.get("external_id")]
        if not openalex_papers:
            return papers

        seeds = sorted(
            openalex_papers,
            key=lambda paper: paper.get("citation_count") or 0,
            reverse=True,
        )[: self.settings.retrieval_openalex_citation_expansion_seeds]

        openalex = self._openalex_client(metrics)
        expanded = list(papers)
        seen = {str(p.get("doi") or p.get("external_id") or p.get("title")).lower() for p in papers}

        for seed in seeds:
            work_id = extract_openalex_work_id(str(seed.get("external_id") or ""))
            if not work_id:
                continue
            for mode in ("cites", "related_to"):
                try:
                    batch = await openalex.fetch_expansion(
                        client,
                        work_id=work_id,
                        limit=self.settings.retrieval_openalex_citation_expansion_limit,
                        mode=mode,
                    )
                except Exception as exc:
                    logger.warning(
                        "openalex_expansion_failed",
                        work_id=work_id,
                        mode=mode,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                for paper in batch:
                    key = str(paper.get("doi") or paper.get("external_id") or paper.get("title")).lower()
                    if key and key not in seen:
                        expanded.append(paper)
                        seen.add(key)

        if len(expanded) > len(papers):
            logger.info(
                "openalex_citation_expansion",
                seeds=len(seeds),
                added=len(expanded) - len(papers),
                research_area=research_area,
                topics=topics[:3],
            )
        return expanded

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
