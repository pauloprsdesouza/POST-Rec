"""HTTP clients for academic paper source APIs."""

from __future__ import annotations

import time
from typing import Any

import feedparser
import httpx

from apps.api.features.retrieval.normalizers import (
    nested_get,
    normalize_core_work,
    normalize_crossref_work,
    normalize_openalex_work,
    normalize_semantic_scholar_paper,
)
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

ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENALEX_API_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_RECOMMENDATIONS_URL = "https://api.semanticscholar.org/recommendations/v1/papers/"

OPENALEX_SELECT_FIELDS = (
    "id,title,doi,publication_year,cited_by_count,abstract_inverted_index,"
    "authorships,primary_location,type,is_retracted,primary_topic,topics,"
    "open_access,fwci,referenced_works,related_works,keywords"
)
OPENALEX_RATE_LIMIT_URL = "https://api.openalex.org/rate-limit"

SEMANTIC_SCHOLAR_FIELDS = "paperId,title,abstract,authors,year,venue,citationCount,externalIds,url,openAccessPdf"
CROSSREF_API_URL = "https://api.crossref.org/works"
CORE_SEARCH_WORKS_PATH = "/search/works/"


def raise_retryable(exc: Exception, *, source: str) -> None:
    if isinstance(exc, RetryableFetchError):
        raise exc
    if isinstance(exc, httpx.HTTPStatusError):
        from apps.api.shared.infra.http_retry import compute_backoff

        status = exc.response.status_code
        raise RetryableFetchError(
            str(exc) or exc.response.reason_phrase or "HTTP error",
            retry_after_seconds=compute_backoff(
                attempt=1,
                base_delay=10.0 if source == "arxiv" else 5.0,
                status_code=status,
            ),
            status_code=status,
        ) from exc
    raise RetryableFetchError(
        f"{type(exc).__name__}: {exc or 'unknown error'}",
        retry_after_seconds=10.0 if source == "arxiv" else 5.0,
    ) from exc


class AcademicSourceClient:
    """Fetch and normalize papers from external academic APIs."""

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

    def contact_headers(self, service_name: str) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        email = self.settings.crossref_email or self.settings.openalex_email
        if email:
            headers["User-Agent"] = f"POST-Rec/0.1 ({service_name}; mailto:{email})"
        return headers

    def _openalex_filter_config(self, *, tier: str | None = None) -> OpenAlexFilterConfig:
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

    def openalex_filters(
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
            config=self._openalex_filter_config(tier=tier),
        )

    def _normalize_openalex_batch(
        self, works: list[Any], *, query: str, context: str
    ) -> list[dict[str, Any]]:
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

    async def _fetch_openalex_raw(
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
        headers = self.contact_headers("OpenAlex")
        per_page = min(limit, self.settings.retrieval_openalex_per_page_max)
        filter_clause = expansion_filter or self.openalex_filters(
            pass_kind,
            research_area=research_area,
            topics=topics,
            tier=tier,
        )
        params: dict[str, Any] = {
            "per_page": per_page,
            "select": OPENALEX_SELECT_FIELDS,
            "filter": filter_clause,
            **openalex_auth_params(api_key=self.settings.openalex_api_key),
        }
        if use_search and query:
            params["search"] = query
        if pass_kind == "sota":
            params["sort"] = "publication_date:desc"
        else:
            params["sort"] = "cited_by_count:desc"

        try:
            resp = await get_with_retry(
                client,
                OPENALEX_API_URL,
                params=params,
                headers=headers,
                source="openalex",
                retries=self.settings.retrieval_http_retries,
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc, source="openalex")

        if not isinstance(data, dict):
            data = {}

        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        logger.info(
            "openalex_fetch_ok",
            query=query,
            pass_kind=pass_kind,
            tier=tier,
            use_search=use_search,
            result_count=len(data.get("results") or []),
            total_count=meta.get("count"),
            cost_usd=meta.get("cost_usd"),
            filter=filter_clause,
        )
        papers = self._normalize_openalex_batch(
            data.get("results") or [],
            query=query or "",
            context=f"{pass_kind}:{tier}",
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

    async def fetch_openalex(
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
        search_enabled = (
            self.settings.retrieval_openalex_use_search if use_search is None else use_search
        )
        papers, meta = await self._fetch_openalex_raw(
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
            recall_papers, _ = await self._fetch_openalex_raw(
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

    async def fetch_openalex_expansion(
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
        papers, _ = await self._fetch_openalex_raw(
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

    async def fetch_openalex_by_dois(
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
                    headers=self.contact_headers("OpenAlex"),
                    source="openalex",
                    retries=self.settings.retrieval_http_retries,
                )
                data = resp.json()
            except Exception as exc:
                raise_retryable(exc, source="openalex")

            if not isinstance(data, dict):
                data = {}
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            papers = self._normalize_openalex_batch(
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

    async def fetch_openalex_rate_limit(self, client: httpx.AsyncClient) -> dict[str, Any]:
        if not self.settings.openalex_api_key:
            return {}
        try:
            resp = await client.get(
                OPENALEX_RATE_LIMIT_URL,
                params=openalex_auth_params(api_key=self.settings.openalex_api_key),
                headers=self.contact_headers("OpenAlex"),
                timeout=10.0,
            )
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            logger.warning("openalex_rate_limit_fetch_failed", error=str(exc))
            return {}

    async def fetch_arxiv(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "sota"
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        search_query = query if query.startswith(("ti:", "abs:", "cat:", "all:", "(")) else f"all:{query}"
        params: dict[str, Any] = {
            "search_query": search_query,
            "max_results": min(limit, self.settings.retrieval_arxiv_max_results),
        }
        if pass_kind == "sota":
            params["sortBy"] = "submittedDate"
            params["sortOrder"] = "descending"

        try:
            resp = await get_with_retry(
                client,
                ARXIV_API_URL,
                params=params,
                retries=self.settings.retrieval_http_retries,
                base_delay=5.0,
                source="arxiv",
            )
            feed = feedparser.parse(resp.text)
        except Exception as exc:
            raise_retryable(exc, source="arxiv")

        if getattr(feed, "bozo", False) and not feed.entries:
            raise RetryableFetchError(
                f"arXiv feed parse error: {getattr(feed, 'bozo_exception', 'invalid feed')}",
                retry_after_seconds=10.0,
            )

        results: list[dict[str, Any]] = []
        for entry in getattr(feed, "entries", []) or []:
            if entry is None:
                continue
            entry_get = getattr(entry, "get", None)
            if not callable(entry_get):
                continue
            title = str(entry_get("title", "") or "").replace("\n", " ").strip()
            if not title:
                continue
            published = entry_get("published")
            year = int(str(published)[:4]) if published else None
            results.append(
                {
                    "external_id": entry_get("id"),
                    "source": "arxiv",
                    "title": title,
                    "abstract": str(entry_get("summary", "") or "").replace("\n", " ").strip() or None,
                    "authors": [a.name for a in entry_get("authors", []) if getattr(a, "name", None)],
                    "year": year,
                    "venue": "arXiv",
                    "doi": None,
                    "url": entry_get("link"),
                    "citation_count": 0,
                }
            )

        return results

    async def fetch_semantic_scholar(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        headers = self.contact_headers("SemanticScholar")
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key

        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, self.settings.retrieval_semantic_scholar_limit_max),
            "fields": SEMANTIC_SCHOLAR_FIELDS,
            "year": f"{self._article_age_cutoff}-",
        }

        try:
            resp = await get_with_retry(
                client,
                SEMANTIC_SCHOLAR_API_URL,
                params=params,
                headers=headers,
                retries=self.settings.retrieval_http_retries,
                base_delay=5.0,
                source="semantic_scholar",
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc, source="semantic_scholar")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        for paper in data.get("data") or []:
            if not isinstance(paper, dict):
                continue
            try:
                normalized = normalize_semantic_scholar_paper(paper)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "semantic_scholar_record_skipped",
                    query=query,
                    paper_id=paper.get("paperId"),
                    error=str(exc),
                )

        return results

    async def fetch_crossref(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        headers = self.contact_headers("Crossref")
        cutoff = self._article_age_cutoff
        filters = ["has-abstract:true", f"from-pub-date:{cutoff}-01-01"]
        params: dict[str, Any] = {
            "query": query,
            "rows": min(limit, self.settings.retrieval_crossref_rows_max),
            "filter": ",".join(filters),
        }
        if pass_kind == "sota":
            params["sort"] = "published"
            params["order"] = "desc"
        else:
            params["sort"] = "is-referenced-by-count"
            params["order"] = "desc"
        if self.settings.crossref_email:
            params["mailto"] = self.settings.crossref_email
        try:
            resp = await get_with_retry(
                client,
                CROSSREF_API_URL,
                params=params,
                headers=headers,
                source="crossref",
                retries=self.settings.retrieval_http_retries,
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc, source="crossref")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        for item in nested_get(data, "message", "items", default=[]) or []:
            if not isinstance(item, dict):
                continue
            try:
                normalized = normalize_crossref_work(item)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "crossref_record_skipped",
                    query=query,
                    doi=item.get("DOI"),
                    error=str(exc),
                )

        return results

    def core_headers(self) -> dict[str, str]:
        headers = self.contact_headers("CORE")
        if self.settings.core_api_key:
            headers["Authorization"] = f"Bearer {self.settings.core_api_key}"
        return headers

    def core_search_url(self) -> str:
        base = self.settings.core_api_base_url.rstrip("/")
        return f"{base}{CORE_SEARCH_WORKS_PATH}"

    async def fetch_core(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        if limit <= 0 or not self.settings.core_api_key:
            return []

        params: dict[str, Any] = {
            "q": query,
            "limit": min(limit, self.settings.retrieval_core_limit_max),
            "offset": 0,
        }
        if pass_kind == "sota":
            params["sort"] = "recency"

        try:
            resp = await get_with_retry(
                client,
                self.core_search_url(),
                params=params,
                headers=self.core_headers(),
                source="core",
                retries=self.settings.retrieval_http_retries,
                base_delay=10.0,
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc, source="core")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        for work in data.get("results") or []:
            if not isinstance(work, dict):
                continue
            try:
                normalized = normalize_core_work(work)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "core_record_skipped",
                    query=query,
                    work_id=work.get("id"),
                    error=str(exc),
                )

        return results

    async def fetch_semantic_scholar_recommendations_for_seeds(
        self,
        client: httpx.AsyncClient,
        seed_ids: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        if not seed_ids:
            return []

        headers = self.contact_headers("SemanticScholar")
        headers["Content-Type"] = "application/json"
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key

        params = {
            "fields": SEMANTIC_SCHOLAR_FIELDS,
            "limit": min(limit, 500),
        }
        body = {"positivePaperIds": seed_ids, "negativePaperIds": []}

        try:
            resp = await get_with_retry(
                client,
                SEMANTIC_SCHOLAR_RECOMMENDATIONS_URL,
                params=params,
                headers=headers,
                json=body,
                method="POST",
                retries=self.settings.retrieval_http_retries,
                base_delay=5.0,
                source="semantic_scholar",
            )
            data = resp.json()
        except Exception as exc:
            raise_retryable(exc, source="semantic_scholar")

        if not isinstance(data, dict):
            data = {}

        seed_set = set(seed_ids)
        results: list[dict[str, Any]] = []
        for paper in data.get("recommendedPapers") or data.get("data") or []:
            if not isinstance(paper, dict):
                continue
            paper_id = str(paper.get("paperId") or "").strip()
            if paper_id and paper_id in seed_set:
                continue
            try:
                normalized = normalize_semantic_scholar_paper(paper)
                if normalized:
                    normalized["retrieval_pass"] = "recommendations"
                    results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "semantic_scholar_recommendation_skipped",
                    paper_id=paper.get("paperId"),
                    error=str(exc),
                )
        return results
