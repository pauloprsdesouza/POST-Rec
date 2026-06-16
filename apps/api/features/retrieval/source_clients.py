"""OpenAlex HTTP client for academic paper retrieval."""

from __future__ import annotations

import time
from typing import Any

import httpx

from apps.api.features.retrieval.normalizers import normalize_openalex_work
from apps.api.shared.infra.http_retry import RetryableFetchError, get_with_retry
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import Settings
from packages.postrec_core.retrieval.openalex_metrics import OpenAlexRunMetrics
from packages.postrec_core.retrieval.openalex_query import (
    OpenAlexFilterConfig,
    build_openalex_expansion_filters,
    build_openalex_work_filters,
    openalex_auth_params,
)

logger = get_logger("postrec-retrieval-sources")

OPENALEX_API_URL = "https://api.openalex.org/works"
OPENALEX_RATE_LIMIT_URL = "https://api.openalex.org/rate-limit"
OPENALEX_SELECT_FIELDS = (
    "id,title,doi,publication_year,cited_by_count,abstract_inverted_index,"
    "authorships,primary_location,type,is_retracted,primary_topic,topics,"
    "open_access,fwci,referenced_works,related_works,keywords"
)


def raise_retryable(exc: Exception, *, source: str = "openalex") -> None:
    if isinstance(exc, RetryableFetchError):
        raise exc
    if isinstance(exc, httpx.HTTPStatusError):
        from apps.api.shared.infra.http_retry import compute_backoff

        status = exc.response.status_code
        raise RetryableFetchError(
            str(exc) or exc.response.reason_phrase or "HTTP error",
            retry_after_seconds=compute_backoff(attempt=1, base_delay=5.0, status_code=status),
            status_code=status,
        ) from exc
    raise RetryableFetchError(
        f"{type(exc).__name__}: {exc or 'unknown error'}",
        retry_after_seconds=5.0,
    ) from exc


class OpenAlexClient:
    """Fetch and normalize papers from OpenAlex."""

    def __init__(
        self,
        settings: Settings,
        article_age_cutoff: int,
        *,
        metrics: OpenAlexRunMetrics | None = None,
    ) -> None:
        self.settings = settings
        self._article_age_cutoff = article_age_cutoff
        self._metrics = metrics

    def contact_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.settings.openalex_email:
            headers["User-Agent"] = f"POST-Rec/0.1 (OpenAlex; mailto:{self.settings.openalex_email})"
        return headers

    def _filter_config(self, *, tier: str | None = None) -> OpenAlexFilterConfig:
        return OpenAlexFilterConfig(
            tier=tier or self.settings.retrieval_openalex_filter_tier,
            use_field_filter=self.settings.retrieval_openalex_field_filter_enabled,
            use_subfield_filter=self.settings.retrieval_openalex_subfield_filter_enabled,
            use_topic_filter=self.settings.retrieval_openalex_topic_filter_enabled,
            require_core_source=self.settings.retrieval_openalex_require_core_source,
            topic_min_relevance=self.settings.retrieval_openalex_topic_min_relevance,
            foundation_min_citations=self.settings.retrieval_openalex_foundation_min_citations,
            sota_min_citations=self.settings.retrieval_openalex_sota_min_citations,
            open_access_only=self.settings.retrieval_openalex_open_access_only,
        )

    def work_filters(
        self,
        pass_kind: str,
        *,
        research_area: str | None = None,
        topics: list[str] | None = None,
        tier: str | None = None,
    ) -> str:
        return build_openalex_work_filters(
            article_age_cutoff=self._article_age_cutoff,
            pass_kind=pass_kind,
            research_area=research_area,
            topics=topics,
            config=self._filter_config(tier=tier),
        )

    def _normalize_batch(self, works: list[Any], *, query: str, context: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for work in works:
            if not isinstance(work, dict):
                continue
            try:
                normalized = normalize_openalex_work(work)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "openalex_record_skipped",
                    query=query,
                    context=context,
                    work_id=work.get("id"),
                    error=str(exc),
                )
        return results

    async def _fetch_raw(
        self,
        client: httpx.AsyncClient,
        *,
        query: str | None,
        limit: int,
        pass_kind: str,
        research_area: str | None,
        topics: list[str] | None,
        tier: str,
        use_search: bool,
        expansion_filter: str | None = None,
        fetch_kind: str = "search",
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        started = time.perf_counter()
        filter_clause = expansion_filter or self.work_filters(
            pass_kind,
            research_area=research_area,
            topics=topics,
            tier=tier,
        )
        params: dict[str, Any] = {
            "per_page": min(limit, self.settings.retrieval_openalex_per_page_max),
            "select": OPENALEX_SELECT_FIELDS,
            "filter": filter_clause,
            **openalex_auth_params(api_key=self.settings.openalex_api_key),
        }
        if use_search and query:
            params["search"] = query
        params["sort"] = "publication_date:desc" if pass_kind == "sota" else "cited_by_count:desc"

        try:
            resp = await get_with_retry(
                client,
                OPENALEX_API_URL,
                params=params,
                headers=self.contact_headers(),
                source="openalex",
                retries=self.settings.retrieval_http_retries,
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc)

        if not isinstance(data, dict):
            data = {}
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        papers = self._normalize_batch(
            data.get("results") or [],
            query=query or "",
            context=f"{pass_kind}:{tier}",
        )
        logger.info(
            "openalex_fetch_ok",
            query=query,
            pass_kind=pass_kind,
            tier=tier,
            use_search=use_search,
            result_count=len(papers),
            total_count=meta.get("count"),
            cost_usd=meta.get("cost_usd"),
            filter=filter_clause,
        )
        if self._metrics is not None:
            cost_usd = meta.get("cost_usd")
            self._metrics.record_fetch(
                result_count=len(papers),
                cost_usd=float(cost_usd) if cost_usd is not None else None,
                latency_ms=(time.perf_counter() - started) * 1000,
                use_search=use_search and bool(query),
                kind=fetch_kind,
            )
        return papers, meta

    async def fetch_works(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
        pass_kind: str = "foundation",
        *,
        research_area: str | None = None,
        topics: list[str] | None = None,
        tier: str | None = None,
        use_search: bool | None = None,
    ) -> list[dict[str, Any]]:
        active_tier = tier or self.settings.retrieval_openalex_filter_tier
        search_enabled = self.settings.retrieval_openalex_use_search if use_search is None else use_search
        papers, meta = await self._fetch_raw(
            client,
            query=query,
            limit=limit,
            pass_kind=pass_kind,
            research_area=research_area,
            topics=topics,
            tier=active_tier,
            use_search=search_enabled,
        )

        if (
            self.settings.retrieval_openalex_fallback_recall_enabled
            and active_tier != "recall"
            and len(papers) < self.settings.retrieval_openalex_fallback_min_results
        ):
            logger.info(
                "openalex_recall_fallback",
                query=query,
                pass_kind=pass_kind,
                initial_count=len(papers),
                total_count=meta.get("count"),
            )
            recall_papers, _ = await self._fetch_raw(
                client,
                query=query,
                limit=limit,
                pass_kind=pass_kind,
                research_area=research_area,
                topics=topics,
                tier="recall",
                use_search=search_enabled,
                fetch_kind="fallback",
            )
            seen = {paper.get("doi") or paper.get("external_id") or paper.get("title") for paper in papers}
            for paper in recall_papers:
                key = paper.get("doi") or paper.get("external_id") or paper.get("title")
                if key and key not in seen:
                    papers.append(paper)
                    seen.add(key)
        return papers

    async def fetch_expansion(
        self,
        client: httpx.AsyncClient,
        *,
        work_id: str,
        limit: int,
        mode: str,
    ) -> list[dict[str, Any]]:
        expansion_filter = build_openalex_expansion_filters(
            article_age_cutoff=self._article_age_cutoff,
            work_id=work_id,
            mode=mode,
        )
        papers, _ = await self._fetch_raw(
            client,
            query=None,
            limit=limit,
            pass_kind="foundation",
            research_area=None,
            topics=None,
            tier="recall",
            use_search=False,
            expansion_filter=expansion_filter,
            fetch_kind=f"expansion_{mode}",
        )
        for paper in papers:
            paper["retrieval_pass"] = f"expansion_{mode}"
        return papers

    async def fetch_by_dois(
        self,
        client: httpx.AsyncClient,
        dois: list[str],
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        cleaned = [doi.strip() for doi in dois if doi and str(doi).strip()]
        if not cleaned:
            return []

        batch_size = max(1, self.settings.retrieval_openalex_doi_batch_size)
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for offset in range(0, len(cleaned), batch_size):
            batch = cleaned[offset : offset + batch_size]
            filter_clause = f"doi:{'|'.join(batch)}"
            params: dict[str, Any] = {
                "per_page": min(limit, len(batch), self.settings.retrieval_openalex_per_page_max),
                "select": OPENALEX_SELECT_FIELDS,
                "filter": filter_clause,
                **openalex_auth_params(api_key=self.settings.openalex_api_key),
            }
            started = time.perf_counter()
            try:
                resp = await get_with_retry(
                    client,
                    OPENALEX_API_URL,
                    params=params,
                    headers=self.contact_headers(),
                    source="openalex",
                    retries=self.settings.retrieval_http_retries,
                )
                data = resp.json()
            except Exception as exc:
                raise_retryable(exc)

            if not isinstance(data, dict):
                data = {}
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            papers = self._normalize_batch(
                data.get("results") or [],
                query="|".join(batch),
                context="doi_batch",
            )
            if self._metrics is not None:
                cost_usd = meta.get("cost_usd")
                self._metrics.record_fetch(
                    result_count=len(papers),
                    cost_usd=float(cost_usd) if cost_usd is not None else None,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    use_search=False,
                    kind="doi_batch",
                )
            for paper in papers:
                key = paper.get("doi") or paper.get("external_id") or paper.get("title")
                if key and key not in seen:
                    results.append(paper)
                    seen.add(str(key))
        return results

    async def fetch_rate_limit(self, client: httpx.AsyncClient) -> dict[str, Any]:
        if not self.settings.openalex_api_key:
            return {}
        try:
            resp = await client.get(
                OPENALEX_RATE_LIMIT_URL,
                params=openalex_auth_params(api_key=self.settings.openalex_api_key),
                headers=self.contact_headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            logger.warning("openalex_rate_limit_fetch_failed", error=str(exc))
            return {}


# Backward-compatible alias used by retrieval service.
AcademicSourceClient = OpenAlexClient
