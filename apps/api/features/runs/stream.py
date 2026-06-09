"""Async Redis subscription for run SSE streams."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import redis.asyncio as aioredis
from sqlalchemy.orm import Session

from apps.api.features.runs.query import run_stream_payload
from apps.api.features.runs.stream_service import CHANNEL_PREFIX
from apps.api.shared.infra.cache import is_terminal_run
from apps.api.shared.models import RecommendationRun
from apps.api.shared.settings import get_settings


def format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def stream_run_updates(db: Session, run: RecommendationRun) -> AsyncIterator[str]:
    """Yield SSE frames: initial snapshot, live Redis updates, heartbeats, then complete."""
    settings = get_settings()
    run_id = str(run.id)
    channel = f"{CHANNEL_PREFIX}{run_id}"

    snapshot = run_stream_payload(db, run)
    yield format_sse("run_update", json.dumps(snapshot, default=str))

    if is_terminal_run(run.status):
        yield format_sse("complete", "{}")
        return

    if not settings.run_stream_enabled or not settings.redis_url:
        yield format_sse("complete", "{}")
        return

    client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=15.0,
            )
            if message and message.get("type") == "message":
                raw = message.get("data")
                if not raw:
                    await asyncio.sleep(0)
                    continue
                yield format_sse("run_update", raw)
                try:
                    payload = json.loads(raw)
                    status = payload.get("run", {}).get("status")
                    if status and is_terminal_run(status):
                        yield format_sse("complete", "{}")
                        break
                except json.JSONDecodeError:
                    pass
            else:
                yield format_sse("ping", "{}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await client.aclose()
