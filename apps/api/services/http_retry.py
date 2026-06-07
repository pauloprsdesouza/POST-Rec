"""HTTP retry helpers with full jitter (AWS-style) for external academic APIs."""

import asyncio
import random
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class RetryableFetchError(Exception):
    """Raised when a fetch should be retried after a delay."""

    def __init__(self, message: str, *, retry_after_seconds: float, status_code: int | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.status_code = status_code


def full_jitter_backoff(
    *,
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 120.0,
    status_code: int | None = None,
) -> float:
    """AWS recommended backoff: sleep = random(0, min(cap, base * 2^attempt))."""
    if status_code == 429:
        base_delay = max(base_delay, 5.0)
        max_delay = max(max_delay, 90.0)
    ceiling = min(base_delay * (2 ** max(attempt, 0)), max_delay)
    return random.uniform(0.0, ceiling)


def parse_retry_after(response: httpx.Response, *, attempt: int, base_delay: float) -> float:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return max(float(header), base_delay)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(header)
                from datetime import UTC, datetime

                delta = (retry_at - datetime.now(UTC)).total_seconds()
                return max(delta, base_delay)
            except (TypeError, ValueError, OverflowError):
                pass

    return full_jitter_backoff(attempt=attempt, base_delay=base_delay, status_code=response.status_code)


def compute_backoff(
    *,
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 120.0,
    status_code: int | None = None,
) -> float:
    return full_jitter_backoff(
        attempt=max(attempt - 1, 0),
        base_delay=base_delay,
        max_delay=max_delay,
        status_code=status_code,
    )


async def get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 120.0,
    source: str | None = None,
) -> httpx.Response:
    last_response: httpx.Response | None = None
    last_exc: Exception | None = None

    source_min_delay = {
        "arxiv": 8.0,
        "semantic_scholar": 6.0,
    }

    for attempt in range(retries):
        try:
            response = await client.get(url, params=params, headers=headers)
            last_response = response
            if response.status_code not in RETRYABLE_STATUS_CODES:
                response.raise_for_status()
                return response

            retry_after = parse_retry_after(response, attempt=attempt, base_delay=base_delay)
            if source in source_min_delay and response.status_code == 429:
                retry_after = max(retry_after, source_min_delay[source])
            if attempt >= retries - 1:
                response.raise_for_status()

            await asyncio.sleep(retry_after)
        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt >= retries - 1:
                raise RetryableFetchError(
                    f"Timeout after {retries} attempts",
                    retry_after_seconds=compute_backoff(
                        attempt=attempt + 1,
                        base_delay=base_delay,
                        max_delay=max_delay,
                    ),
                ) from exc
            await asyncio.sleep(
                compute_backoff(
                    attempt=attempt + 1,
                    base_delay=base_delay,
                    max_delay=max_delay,
                )
            )
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code not in RETRYABLE_STATUS_CODES or attempt >= retries - 1:
                raise RetryableFetchError(
                    str(exc) or exc.response.reason_phrase or "HTTP error",
                    retry_after_seconds=compute_backoff(
                        attempt=attempt + 1,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        status_code=exc.response.status_code,
                    ),
                    status_code=exc.response.status_code,
                ) from exc
            delay = parse_retry_after(exc.response, attempt=attempt, base_delay=base_delay)
            if source in source_min_delay and exc.response.status_code == 429:
                delay = max(delay, source_min_delay[source])
            await asyncio.sleep(delay)

    if last_response is not None:
        last_response.raise_for_status()
    if last_exc:
        raise last_exc
    raise RetryableFetchError("Request failed", retry_after_seconds=base_delay)
