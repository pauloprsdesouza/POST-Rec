"""Redis-backed cache for academic source fetch results."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from apps.api.observability.logging import get_logger
from apps.api.settings import get_settings

logger = get_logger("postrec-retrieval-cache")


class RetrievalCacheService:
    """Cache fetch results to avoid repeat 429 storms across runs."""

    def __init__(self) -> None:
        self._redis = None
        settings = get_settings()
        self._enabled = settings.retrieval_cache_enabled
        self._ttl = settings.retrieval_cache_ttl_seconds
        self._prefix = settings.cache_key_prefix
        if self._enabled and settings.redis_url:
            try:
                import redis

                self._redis = redis.from_url(settings.redis_url, socket_connect_timeout=2)
                self._redis.ping()
            except Exception as exc:
                logger.warning("retrieval_cache_redis_unavailable", error=str(exc))
                self._redis = None

    def _key(
        self,
        source: str,
        query: str,
        limit: int,
        pass_kind: str,
        job_type: str = "search",
    ) -> str:
        digest = hashlib.sha256(
            f"{job_type}|{source}|{query.strip().lower()}|{limit}|{pass_kind}".encode()
        ).hexdigest()[:24]
        return f"{self._prefix}:fetch:{source}:{digest}"

    def get(
        self,
        source: str,
        query: str,
        limit: int,
        pass_kind: str,
        job_type: str = "search",
    ) -> list[dict[str, Any]] | None:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(self._key(source, query, limit, pass_kind, job_type))
            if not raw:
                return None
            payload = json.loads(raw)
            if isinstance(payload, list):
                logger.info("retrieval_cache_hit", source=source, query=query[:80], count=len(payload))
                return payload
        except Exception as exc:
            logger.warning("retrieval_cache_read_failed", source=source, error=str(exc))
        return None

    def set(
        self,
        source: str,
        query: str,
        limit: int,
        pass_kind: str,
        papers: list[dict[str, Any]],
        job_type: str = "search",
    ) -> None:
        if not self._redis or not papers:
            return
        try:
            self._redis.set(
                self._key(source, query, limit, pass_kind, job_type),
                json.dumps(papers, default=str),
                ex=self._ttl,
            )
        except Exception as exc:
            logger.warning("retrieval_cache_write_failed", source=source, error=str(exc))


retrieval_cache_service = RetrievalCacheService()
