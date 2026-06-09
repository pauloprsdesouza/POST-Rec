"""Redis pub/sub push notifications for live run status and activity logs."""

from __future__ import annotations

import json
import uuid

import redis
from sqlalchemy.orm import Session

from apps.api.features.runs.query import run_stream_payload
from apps.api.shared.database import SessionLocal
from apps.api.shared.models import RecommendationRun
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-run-stream")

CHANNEL_PREFIX = "postrec:run:stream:"


class RunStreamService:
    """Publish run snapshots to Redis; API workers subscribe and stream via SSE."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._enabled = False
        self._configure()

    def _configure(self) -> None:
        settings = get_settings()
        self._enabled = settings.run_stream_enabled and bool(settings.redis_url)
        if not self._enabled:
            return
        try:
            self._client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._client.ping()
            logger.info("run_stream_redis_connected")
        except Exception as exc:
            logger.warning("run_stream_redis_unavailable", error=str(exc))
            self._client = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def channel(self, run_id: str) -> str:
        return f"{CHANNEL_PREFIX}{run_id}"

    def publish(self, db: Session, run: RecommendationRun) -> None:
        if not self.enabled or not self._client:
            return
        try:
            payload = run_stream_payload(db, run)
            self._client.publish(self.channel(str(run.id)), json.dumps(payload, default=str))
        except Exception as exc:
            logger.warning("run_stream_publish_failed", run_id=str(run.id), error=str(exc))

    def publish_by_id(self, run_id: str | uuid.UUID) -> None:
        if not self.enabled:
            return
        db = SessionLocal()
        try:
            run = db.query(RecommendationRun).filter_by(id=uuid.UUID(str(run_id))).first()
            if run:
                self.publish(db, run)
        finally:
            db.close()


run_stream_service = RunStreamService()
