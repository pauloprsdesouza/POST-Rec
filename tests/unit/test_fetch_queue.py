"""Tests for fetch queue scheduling."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from apps.api.services.fetch_queue import FetchJob, FetchQueueProcessor
from apps.api.services.http_retry import RetryableFetchError


@pytest.mark.asyncio
async def test_fetch_queue_requeues_retryable_errors(monkeypatch):
    calls = {"count": 0}

    async def handler(job: FetchJob):
        calls["count"] += 1
        if calls["count"] < 3:
            raise RetryableFetchError("rate limited", retry_after_seconds=0.01, status_code=429)
        return [{"title": "Paper", "source": job.source, "citation_count": 1}]

    async def noop_wait(_source: str):
        return None

    monkeypatch.setattr(
        "apps.api.services.fetch_queue.source_rate_limiter.wait_async",
        noop_wait,
    )

    processor = FetchQueueProcessor(handler, max_attempts=4)
    result = await processor.process([FetchJob(source="arxiv", query="test", limit=3)])

    assert calls["count"] == 3
    assert len(result.papers) == 1
    assert result.requeued_jobs == 2
    assert result.exhausted_jobs == []


@pytest.mark.asyncio
async def test_fetch_queue_exhausts_after_max_attempts(monkeypatch):
    async def handler(job: FetchJob):
        raise RetryableFetchError("always failing", retry_after_seconds=0.01, status_code=429)

    async def noop_wait(_source: str):
        return None

    monkeypatch.setattr(
        "apps.api.services.fetch_queue.source_rate_limiter.wait_async",
        noop_wait,
    )

    processor = FetchQueueProcessor(handler, max_attempts=2)
    result = await processor.process([FetchJob(source="semantic_scholar", query="test", limit=3)])

    assert result.papers == []
    assert len(result.exhausted_jobs) == 1
