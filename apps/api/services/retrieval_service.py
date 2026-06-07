"""Academic paper retrieval from multiple open sources."""

import asyncio
import hashlib
import re
import sys
from typing import Any

import feedparser
import httpx
from sqlalchemy.orm import Session

from apps.api.models import SourceDocument
from apps.api.observability.logging import get_logger
from apps.api.services.fetch_queue import FetchJob, FetchQueueProcessor
from apps.api.services.http_retry import RetryableFetchError, get_with_retry
from apps.api.services.resilience.registry import get_source_circuit_breaker
from apps.api.services.retrieval_cache import retrieval_cache_service
from apps.api.services.relevance_service import filter_and_rank_papers
from apps.api.settings import get_settings
from packages.postrec_core.retrieval.dual_pass import merge_dual_pass_results
from packages.postrec_core.retrieval.paper_enrichment import enrich_paper_metadata
from packages.postrec_core.retrieval.paper_tier import current_year
from packages.postrec_core.retrieval.query_expansion import expand_retrieval_queries

logger = get_logger("postrec-retrieval")

ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENALEX_API_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API_URL = "https://api.crossref.org/works"

SEMANTIC_SCHOLAR_FIELDS = (
    "paperId,title,abstract,authors,year,venue,citationCount,externalIds,url,openAccessPdf"
)

SOURCE_FETCHERS = ("openalex", "arxiv", "semantic_scholar", "crossref")


def _content_hash(title: str, abstract: str | None) -> str:
    content = f"{title}|{abstract or ''}"
    return hashlib.sha256(content.encode()).hexdigest()


def _normalize_doi(doi: Any) -> str | None:
    if not doi:
        return None
    value = str(doi).strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value or None


def _nested_get(data: Any, *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def _normalize_openalex_work(work: dict[str, Any]) -> dict[str, Any] | None:
    title = work.get("title") or work.get("display_name")
    if not title:
        return None

    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        name = _nested_get(authorship, "author", "display_name")
        if name:
            authors.append(str(name))

    inverted_index = work.get("abstract_inverted_index")
    abstract = _reconstruct_abstract(inverted_index) if isinstance(inverted_index, dict) else None

    return {
        "external_id": work.get("id"),
        "source": "openalex",
        "title": str(title).strip(),
        "abstract": abstract or None,
        "authors": authors or None,
        "year": work.get("publication_year"),
        "venue": _nested_get(work, "primary_location", "source", "display_name"),
        "doi": _normalize_doi(work.get("doi")),
        "url": work.get("id") or work.get("doi"),
        "citation_count": work.get("cited_by_count") or 0,
    }


def _normalize_semantic_scholar_paper(paper: dict[str, Any]) -> dict[str, Any] | None:
    title = paper.get("title")
    if not title:
        return None

    authors = [
        str(a.get("name"))
        for a in paper.get("authors") or []
        if isinstance(a, dict) and a.get("name")
    ]
    external_ids = paper.get("externalIds") or {}
    doi = _normalize_doi(external_ids.get("DOI") if isinstance(external_ids, dict) else None)
    url = paper.get("url")
    pdf = _nested_get(paper, "openAccessPdf", "url")
    if not url and pdf:
        url = pdf

    return {
        "external_id": paper.get("paperId"),
        "source": "semantic_scholar",
        "title": str(title).strip(),
        "abstract": paper.get("abstract") or None,
        "authors": authors or None,
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "doi": doi,
        "url": url,
        "citation_count": paper.get("citationCount") or 0,
    }


def _normalize_crossref_work(item: dict[str, Any]) -> dict[str, Any] | None:
    titles = item.get("title") or []
    title = titles[0] if titles else None
    if not title:
        return None

    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        given = author.get("given") or ""
        family = author.get("family") or ""
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)

    year = None
    for date_key in ("published-print", "published-online", "created"):
        parts = _nested_get(item, date_key, "date-parts", default=[])
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = parts[0][0]
            break

    venue_parts = item.get("container-title") or []
    venue = venue_parts[0] if venue_parts else None
    doi = _normalize_doi(item.get("DOI"))

    return {
        "external_id": doi or item.get("URL"),
        "source": "crossref",
        "title": str(title).strip(),
        "abstract": _strip_crossref_abstract(item.get("abstract")),
        "authors": authors or None,
        "year": year,
        "venue": venue,
        "doi": doi,
        "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
        "citation_count": item.get("is-referenced-by-count") or 0,
    }


def _strip_crossref_abstract(abstract: Any) -> str | None:
    if not abstract:
        return None
    text = str(abstract)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _reconstruct_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            words.append((pos, word))
    words.sort()
    return " ".join(w for _, w in words)


def _raise_retryable(exc: Exception, *, source: str) -> None:
    if isinstance(exc, RetryableFetchError):
        raise exc
    if isinstance(exc, httpx.HTTPStatusError):
        from apps.api.services.http_retry import compute_backoff

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


class RetrievalService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def retrieve_papers(
        self,
        db: Session,
        topics: list[str],
        max_papers: int = 50,
        *,
        research_area: str | None = None,
        learned_topics: list[str] | None = None,
        avoided_topics: list[str] | None = None,
    ) -> list[SourceDocument]:
        cleaned_topics = [t.strip() for t in topics if t and t.strip()]
        if not cleaned_topics:
            return []

        expanded_queries = expand_retrieval_queries(
            cleaned_topics,
            research_area=research_area,
            learned_topics=learned_topics,
            include_sota_terms=True,
        )

        fetch_target = min(max(max_papers * 2, max_papers + 20), 200)
        per_query = max(fetch_target // max(len(expanded_queries), 1), 10)
        per_source = max(per_query // 4, 5)
        jobs = self._build_fetch_jobs(expanded_queries, per_source)
        jobs.sort(key=lambda job: (job.priority, job.source, job.query))

        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            processor = FetchQueueProcessor(
                lambda job: self._dispatch_job(client, job),
                max_attempts=self.settings.retrieval_fetch_max_attempts,
                circuit_breaker=get_source_circuit_breaker(),
                min_unique_papers=self.settings.retrieval_min_papers_before_skip,
            )
            queue_result = await processor.process(jobs)
            raw_papers = list(queue_result.papers)

            if queue_result.exhausted_jobs:
                deferred = await self._retry_exhausted_fetches(client, queue_result.exhausted_jobs)
                raw_papers.extend(deferred)
                logger.info(
                    "deferred_fetch_complete",
                    requested=len(queue_result.exhausted_jobs),
                    recovered=len(deferred),
                )

        if self.settings.dual_retrieval_enabled:
            sota_papers = [p for p in raw_papers if p.get("retrieval_pass") == "sota"]
            foundation_papers = [p for p in raw_papers if p.get("retrieval_pass") == "foundation"]
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

        papers, filter_stats = filter_and_rank_papers(
            papers,
            topics=cleaned_topics,
            research_area=research_area,
            learned_topics=learned_topics,
            avoided_topics=avoided_topics,
            min_score=self.settings.retrieval_min_relevance_score,
            max_papers=fetch_target,
        )
        saved = self._persist_papers(db, papers, max_papers)

        logger.info(
            "papers_retrieved",
            count=len(saved),
            requested=max_papers,
            sources_collected=len(papers),
            fetch_jobs=len(jobs),
            expanded_queries=len(expanded_queries),
            fetch_requeued=queue_result.requeued_jobs,
            fetch_exhausted=len(queue_result.exhausted_jobs),
            fetch_skipped_circuit=queue_result.skipped_circuit_jobs,
            fetch_early_stopped=queue_result.early_stopped,
            relevance_input=filter_stats["input"],
            relevance_filtered_out=filter_stats["filtered_out"],
            relevance_kept=filter_stats["kept"],
        )
        return saved

    async def fetch_source(
        self, source: str, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            job = FetchJob(source=source, query=query, limit=limit, pass_kind=pass_kind)
            return await self._dispatch_job(client, job)

    def _source_priority_map(self) -> dict[str, int]:
        order = [
            part.strip()
            for part in self.settings.retrieval_source_priority.split(",")
            if part.strip()
        ]
        return {source: index for index, source in enumerate(order)}

    def _build_fetch_jobs(self, queries: list[str], per_source: int) -> list[FetchJob]:
        jobs: list[FetchJob] = []
        priority_map = self._source_priority_map()
        pass_kinds = ("sota", "foundation") if self.settings.dual_retrieval_enabled else ("foundation",)
        for query in queries:
            for pass_kind in pass_kinds:
                sota_limit = max(per_source // 2, 3)
                limit = sota_limit if pass_kind == "sota" else per_source
                specs = (
                    ("openalex", limit),
                    ("arxiv", max(limit // 2, 3)),
                    ("semantic_scholar", limit),
                    ("crossref", limit),
                )
                for source, source_limit in specs:
                    jobs.append(
                        FetchJob(
                            source=source,
                            query=query,
                            limit=source_limit,
                            pass_kind=pass_kind,
                            priority=priority_map.get(source, 99),
                        )
                    )
        return jobs

    async def _dispatch_job(
        self, client: httpx.AsyncClient, job: FetchJob
    ) -> list[dict[str, Any]]:
        cached = retrieval_cache_service.get(job.source, job.query, job.limit, job.pass_kind)
        if cached is not None:
            for paper in cached:
                paper["retrieval_pass"] = job.pass_kind
            return cached

        if job.source == "openalex":
            papers = await self._fetch_openalex(client, job.query, job.limit, job.pass_kind)
        elif job.source == "arxiv":
            papers = await self._fetch_arxiv(client, job.query, job.limit)
        elif job.source == "semantic_scholar":
            papers = await self._fetch_semantic_scholar(client, job.query, job.limit, job.pass_kind)
        elif job.source == "crossref":
            papers = await self._fetch_crossref(client, job.query, job.limit, job.pass_kind)
        else:
            raise ValueError(f"Unknown source: {job.source}")

        for paper in papers:
            paper["retrieval_pass"] = job.pass_kind
        if papers:
            retrieval_cache_service.set(job.source, job.query, job.limit, job.pass_kind, papers)
        return papers

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
        from apps.api.services.source_rate_limiter import source_rate_limiter

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

    def _persist_papers(
        self, db: Session, papers: list[dict[str, Any]], max_papers: int
    ) -> list[SourceDocument]:
        seen_hashes: set[str] = set()
        seen_dois: set[str] = set()
        saved: list[SourceDocument] = []

        for paper in papers:
            if len(saved) >= max_papers:
                break
            if not isinstance(paper, dict) or not paper.get("title") or not paper.get("source"):
                continue

            doi = _normalize_doi(paper.get("doi"))
            if doi:
                if doi in seen_dois:
                    continue
                seen_dois.add(doi)

            ch = _content_hash(paper["title"], paper.get("abstract"))
            if ch in seen_hashes:
                continue
            seen_hashes.add(ch)

            if doi:
                existing = db.query(SourceDocument).filter_by(doi=doi).first()
                if existing:
                    self._merge_paper_metadata(existing, paper)
                    saved.append(existing)
                    continue

            existing = db.query(SourceDocument).filter_by(content_hash=ch).first()
            if existing:
                self._merge_paper_metadata(existing, paper)
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
                content_hash=ch,
                metadata_=paper.get("metadata") or {},
            )
            db.add(doc)
            saved.append(doc)

        db.commit()
        return saved

    @staticmethod
    def _merge_paper_metadata(doc: SourceDocument, paper: dict[str, Any]) -> None:
        metadata = dict(doc.metadata_ or {})
        incoming = paper.get("metadata") if isinstance(paper.get("metadata"), dict) else {}
        for key in ("tier", "retrieval_pass", "methods", "limitations", "hybrid_score", "dense_score"):
            value = paper.get(key)
            if value is None:
                value = incoming.get(key)
            if value is not None:
                metadata[key] = value
        doc.metadata_ = metadata

    def _contact_headers(self, service_name: str) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        email = self.settings.crossref_email or self.settings.openalex_email
        if email:
            headers["User-Agent"] = f"POST-Rec/0.1 ({service_name}; mailto:{email})"
        return headers

    async def _fetch_openalex(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        headers = self._contact_headers("OpenAlex")
        params: dict[str, Any] = {
            "search": query,
            "per_page": min(limit, 25),
        }
        if pass_kind == "sota":
            cutoff = current_year() - self.settings.sota_recent_years
            params["sort"] = "publication_date:desc"
            params["filter"] = f"publication_year:>{cutoff}"
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
            _raise_retryable(exc, source="openalex")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        for work in data.get("results") or []:
            if not isinstance(work, dict):
                continue
            try:
                normalized = _normalize_openalex_work(work)
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

    async def _fetch_arxiv(
        self, client: httpx.AsyncClient, query: str, limit: int
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        try:
            resp = await get_with_retry(
                client,
                ARXIV_API_URL,
                params={"search_query": f"all:{query}", "max_results": min(limit, 10)},
                retries=self.settings.retrieval_http_retries,
                base_delay=5.0,
                source="arxiv",
            )
            feed = feedparser.parse(resp.text)
        except Exception as exc:
            _raise_retryable(exc, source="arxiv")

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
                    "authors": [
                        a.name for a in entry_get("authors", []) if getattr(a, "name", None)
                    ],
                    "year": year,
                    "venue": "arXiv",
                    "doi": None,
                    "url": entry_get("link"),
                    "citation_count": 0,
                }
            )

        return results

    async def _fetch_semantic_scholar(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        headers = self._contact_headers("SemanticScholar")
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key

        try:
            resp = await get_with_retry(
                client,
                SEMANTIC_SCHOLAR_API_URL,
                params={"query": query, "limit": min(limit, 20), "fields": SEMANTIC_SCHOLAR_FIELDS},
                headers=headers,
                retries=self.settings.retrieval_http_retries,
                base_delay=5.0,
                source="semantic_scholar",
            )
            data = resp.json()
        except Exception as exc:
            _raise_retryable(exc, source="semantic_scholar")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        cutoff = current_year() - self.settings.sota_recent_years
        for paper in data.get("data") or []:
            if not isinstance(paper, dict):
                continue
            try:
                normalized = _normalize_semantic_scholar_paper(paper)
                if not normalized:
                    continue
                if pass_kind == "sota":
                    year = normalized.get("year")
                    if isinstance(year, int) and year < cutoff:
                        continue
                results.append(normalized)
            except Exception as exc:
                logger.warning(
                    "semantic_scholar_record_skipped",
                    query=query,
                    paper_id=paper.get("paperId"),
                    error=str(exc),
                )

        return results

    async def _fetch_crossref(
        self, client: httpx.AsyncClient, query: str, limit: int, pass_kind: str = "foundation"
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        headers = self._contact_headers("Crossref")
        params: dict[str, Any] = {
            "query": query,
            "rows": min(limit, 20),
        }
        if pass_kind == "sota":
            cutoff = current_year() - self.settings.sota_recent_years
            params["filter"] = f"from-pub-date:{cutoff}"
            params["sort"] = "published"
            params["order"] = "desc"
        else:
            params["sort"] = "is-referenced-by-count"
            params["order"] = "desc"
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
            _raise_retryable(exc, source="crossref")

        if not isinstance(data, dict):
            data = {}

        results: list[dict[str, Any]] = []
        for item in _nested_get(data, "message", "items", default=[]) or []:
            if not isinstance(item, dict):
                continue
            try:
                normalized = _normalize_crossref_work(item)
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


retrieval_service = RetrievalService()
