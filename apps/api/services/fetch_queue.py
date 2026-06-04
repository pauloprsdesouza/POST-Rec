"""Priority queue scheduler for deferred source fetch retries."""

import asyncio
import heapq
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from apps.api.observability.logging import get_logger
from apps.api.services.http_retry import RetryableFetchError, compute_backoff
from apps.api.services.source_rate_limiter import source_rate_limiter

logger = get_logger("postrec-retrieval")

FetchHandler = Callable[["FetchJob"], Awaitable[list[dict[str, Any]]]]


@dataclass(order=True)
class _QueuedJob:
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


@dataclass
class FetchQueueResult:
    papers: list[dict[str, Any]]
    succeeded_jobs: int
    requeued_jobs: int
    exhausted_jobs: list[FetchJob]


class FetchQueueProcessor:
    """Process fetch jobs with pacing and automatic re-queue on transient errors."""

    def __init__(self, handler: FetchHandler, *, max_attempts: int = 5) -> None:
        self.handler = handler
        self.max_attempts = max_attempts

    async def process(self, jobs: list[FetchJob]) -> FetchQueueResult:
        queue: list[_QueuedJob] = []
        sequence = 0
        for job in jobs:
            job.max_attempts = self.max_attempts
            heapq.heappush(queue, _QueuedJob(time.monotonic(), sequence, job))
            sequence += 1

        papers: list[dict[str, Any]] = []
        succeeded_jobs = 0
        requeued_jobs = 0
        exhausted_jobs: list[FetchJob] = []

        while queue:
            item = heapq.heappop(queue)
            now = time.monotonic()
            if item.run_at > now:
                await asyncio.sleep(item.run_at - now)

            job = item.job
            await source_rate_limiter.wait_async(job.source)

            try:
                batch = await self.handler(job)
                papers.extend(batch)
                succeeded_jobs += 1
                logger.info(
                    "source_fetch_ok",
                    source=job.source,
                    query=job.query,
                    count=len(batch),
                    attempt=job.attempt,
                )
            except RetryableFetchError as exc:
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
                        _QueuedJob(time.monotonic() + delay, sequence, job),
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
                        _QueuedJob(time.monotonic() + delay, sequence, job),
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
        )
