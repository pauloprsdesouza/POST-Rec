"""HTTP clients for academic paper source APIs."""

from __future__ import annotations

from typing import Any

import feedparser
import httpx

from apps.api.features.retrieval.normalizers import (
    nested_get,
    normalize_crossref_work,
    normalize_openalex_work,
    normalize_semantic_scholar_paper,
)
from apps.api.shared.infra.http_retry import RetryableFetchError, get_with_retry
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import Settings

logger = get_logger("postrec-retrieval-sources")

ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENALEX_API_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_RECOMMENDATIONS_URL = "https://api.semanticscholar.org/recommendations/v1/papers/"

OPENALEX_SELECT_FIELDS = (
    "id,title,doi,publication_year,cited_by_count,abstract_inverted_index,authorships,primary_location"
)

SEMANTIC_SCHOLAR_FIELDS = "paperId,title,abstract,authors,year,venue,citationCount,externalIds,url,openAccessPdf"
CROSSREF_API_URL = "https://api.crossref.org/works"


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

    def __init__(self, settings: Settings, article_age_cutoff: int) -> None:
        self.settings = settings
        self._article_age_cutoff = article_age_cutoff

    def contact_headers(self, service_name: str) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        email = self.settings.crossref_email or self.settings.openalex_email
        if email:
            headers["User-Agent"] = f"POST-Rec/0.1 ({service_name}; mailto:{email})"
        return headers

    def openalex_filters(self, pass_kind: str) -> str:
        del pass_kind
        parts = [
            "has_abstract:true",
            "is_paratext:false",
            f"publication_year:>{self._article_age_cutoff}",
        ]
        return ",".join(parts)

    async def fetch_openalex(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        headers = self.contact_headers("OpenAlex")
        per_page = min(limit, self.settings.retrieval_openalex_per_page_max)
        params: dict[str, Any] = {
            "search": query,
            "per_page": per_page,
            "select": OPENALEX_SELECT_FIELDS,
            "filter": self.openalex_filters(pass_kind),
        }
        if pass_kind == "sota":
            params["sort"] = "publication_date:desc"
        else:
            params["sort"] = "cited_by_count:desc"
        if self.settings.openalex_email:
            params["mailto"] = self.settings.openalex_email

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

        results: list[dict[str, Any]] = []
        for work in data.get("results") or []:
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
                    work_id=work.get("id"),
                    error=str(exc),
                )

        return results

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
