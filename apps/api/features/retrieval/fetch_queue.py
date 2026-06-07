"""Priority queue scheduler for deferred source fetch retries."""

import asyncio
import heapq
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.infra.http_retry import RetryableFetchError, compute_backoff
from apps.api.shared.infra.resilience.circuit_breaker import SourceCircuitBreaker, SourceCircuitOpenError
from apps.api.shared.infra.source_rate_limiter import source_rate_limiter

logger = get_logger("postrec-retrieval")

FetchHandler = Callable[["FetchJob"], Awaitable[list[dict[str, Any]]]]
PaperKeyFn = Callable[[dict[str, Any]], str]


def default_paper_key(paper: dict[str, Any]) -> str:
    doi = str(paper.get("doi") or "").lower().strip()
    if doi:
        return f"doi:{doi}"
    title = str(paper.get("title") or "").lower().strip()
    return f"title:{title}" if title else ""


@dataclass(order=True)
class _QueuedJob:
    priority: int
    run_at: float
    sequence: int
    job: "FetchJob" = field(compare=False)


@dataclass
class FetchJob:
    source: str
    query: str
    limit: int
    pass_kind: str = "foundation"
    attempt: int = 1
    max_attempts: int = 5
    priority: int = 50
    job_type: str = "search"
    seed_paper_ids: tuple[str, ...] = ()


@dataclass
class FetchQueueResult:
    papers: list[dict[str, Any]]
    succeeded_jobs: int
    requeued_jobs: int
    exhausted_jobs: list[FetchJob]
    skipped_circuit_jobs: int = 0
    early_stopped: bool = False


class FetchQueueProcessor:
    """Process fetch jobs with pacing, circuit breaking, and early stop."""

    def __init__(
        self,
        handler: FetchHandler,
        *,
        max_attempts: int = 5,
        circuit_breaker: SourceCircuitBreaker | None = None,
        min_unique_papers: int | None = None,
        paper_key: PaperKeyFn = default_paper_key,
    ) -> None:
        self.handler = handler
        self.max_attempts = max_attempts
        self.circuit_breaker = circuit_breaker
        self.min_unique_papers = min_unique_papers
        self.paper_key = paper_key

    def _unique_count(self, papers: list[dict[str, Any]]) -> int:
        keys = {self.paper_key(p) for p in papers if self.paper_key(p)}
        return len(keys)

    def _should_early_stop(self, papers: list[dict[str, Any]], remaining: list[_QueuedJob]) -> bool:
        if not self.min_unique_papers or not remaining:
            return False
        if self._unique_count(papers) < self.min_unique_papers:
            return False
        if not self.circuit_breaker:
            return False
        return all(self.circuit_breaker.is_open(item.job.source) for item in remaining)

    async def process(self, jobs: list[FetchJob]) -> FetchQueueResult:
        queue: list[_QueuedJob] = []
        sequence = 0
        for job in jobs:
            job.max_attempts = self.max_attempts
            heapq.heappush(
                queue,
                _QueuedJob(job.priority, time.monotonic(), sequence, job),
            )
            sequence += 1

        papers: list[dict[str, Any]] = []
        succeeded_jobs = 0
        requeued_jobs = 0
        skipped_circuit_jobs = 0
        exhausted_jobs: list[FetchJob] = []
        early_stopped = False

        while queue:
            if self._should_early_stop(papers, queue):
                skipped = len(queue)
                skipped_circuit_jobs += skipped
                logger.info(
                    "retrieval_early_stop",
                    unique_papers=self._unique_count(papers),
                    min_unique_papers=self.min_unique_papers,
                    skipped_jobs=skipped,
                )
                early_stopped = True
                break

            item = heapq.heappop(queue)
            now = time.monotonic()
            if item.run_at > now:
                await asyncio.sleep(item.run_at - now)

            job = item.job

            if self.circuit_breaker and self.circuit_breaker.is_open(job.source):
                skipped_circuit_jobs += 1
                delay = self.circuit_breaker.seconds_until_closed(job.source)
                logger.info(
                    "source_fetch_circuit_open",
                    source=job.source,
                    query=job.query,
                    retry_after_seconds=round(delay, 2),
                )
                if job.attempt < job.max_attempts:
                    heapq.heappush(
                        queue,
                        _QueuedJob(job.priority, time.monotonic() + max(delay, 1.0), sequence, job),
                    )
                    sequence += 1
                    requeued_jobs += 1
                else:
                    exhausted_jobs.append(job)
                continue

            await source_rate_limiter.wait_async(job.source)

            try:
                if self.circuit_breaker:
                    self.circuit_breaker.before_request(job.source)
                batch = await self.handler(job)
                if self.circuit_breaker:
                    self.circuit_breaker.record_success(job.source)
                papers.extend(batch)
                succeeded_jobs += 1
                logger.info(
                    "source_fetch_ok",
                    source=job.source,
                    query=job.query,
                    count=len(batch),
                    attempt=job.attempt,
                )
            except SourceCircuitOpenError as exc:
                skipped_circuit_jobs += 1
                if job.attempt < job.max_attempts:
                    requeued_jobs += 1
                    heapq.heappush(
                        queue,
                        _QueuedJob(
                            job.priority,
                            time.monotonic() + max(exc.retry_after_seconds, 1.0),
                            sequence,
                            job,
                        ),
                    )
                    sequence += 1
                else:
                    exhausted_jobs.append(job)
            except RetryableFetchError as exc:
                if self.circuit_breaker and exc.status_code in (429, 503):
                    self.circuit_breaker.record_failure(job.source, status_code=exc.status_code)
                job.attempt += 1
                if job.attempt <= job.max_attempts:
                    delay = exc.retry_after_seconds or compute_backoff(
                        attempt=job.attempt,
                        status_code=exc.status_code,
                    )
                    requeued_jobs += 1
                    logger.warning(
                        "source_fetch_requeued",
                        source=job.source,
                        query=job.query,
                        attempt=job.attempt,
                        max_attempts=job.max_attempts,
                        delay_seconds=round(delay, 2),
                        error=str(exc),
                        status_code=exc.status_code,
                    )
                    heapq.heappush(
                        queue,
                        _QueuedJob(job.priority, time.monotonic() + delay, sequence, job),
                    )
                    sequence += 1
                else:
                    exhausted_jobs.append(job)
                    logger.warning(
                        "source_fetch_exhausted",
                        source=job.source,
                        query=job.query,
                        attempts=job.attempt - 1,
                        error=str(exc),
                        status_code=exc.status_code,
                    )
            except Exception as exc:
                job.attempt += 1
                if job.attempt <= job.max_attempts:
                    delay = compute_backoff(attempt=job.attempt)
                    requeued_jobs += 1
                    logger.warning(
                        "source_fetch_requeued",
                        source=job.source,
                        query=job.query,
                        attempt=job.attempt,
                        max_attempts=job.max_attempts,
                        delay_seconds=round(delay, 2),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    heapq.heappush(
                        queue,
                        _QueuedJob(job.priority, time.monotonic() + delay, sequence, job),
                    )
                    sequence += 1
                else:
                    exhausted_jobs.append(job)
                    logger.warning(
                        "source_fetch_exhausted",
                        source=job.source,
                        query=job.query,
                        attempts=job.attempt - 1,
                        error=f"{type(exc).__name__}: {exc}",
                    )

        return FetchQueueResult(
            papers=papers,
            succeeded_jobs=succeeded_jobs,
            requeued_jobs=requeued_jobs,
            exhausted_jobs=exhausted_jobs,
            skipped_circuit_jobs=skipped_circuit_jobs,
            early_stopped=early_stopped,
        )
