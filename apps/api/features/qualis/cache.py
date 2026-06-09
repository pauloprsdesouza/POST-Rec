"""Redis cache-aside layer for Qualis journal lookups."""

from __future__ import annotations

import json
from typing import Any

from apps.api.shared.infra.cache import _cache_redis_url
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-qualis-cache")

# Reference data — long TTL; 0 disables expiry (SET without TTL).
QUALIS_REFERENCE_TTL_DEFAULT = 2_592_000  # 30 days


class QualisCacheKeys:
    @staticmethod
    def issn(normalized_issn: str) -> str:
        return f"qualis:issn:{normalized_issn}"

    @staticmethod
    def title(normalized_title: str) -> str:
        return f"qualis:title:{normalized_title}"


class QualisCache:
    """JSON cache-aside for Qualis estrato lookups on the shared cache Redis DB."""

    def __init__(self) -> None:
        self._client = None
        self._enabled = False
        self._prefix = ""
        self._ttl = QUALIS_REFERENCE_TTL_DEFAULT
        self._configure()

    def _configure(self) -> None:
        settings = get_settings()
        self._prefix = settings.cache_key_prefix
        self._ttl = settings.qualis_cache_ttl
        self._enabled = settings.qualis_use_redis_cache and settings.cache_enabled and bool(settings.redis_url)
        if not self._enabled:
            return
        try:
            import redis

            url = _cache_redis_url(settings.redis_url, settings.cache_redis_db)
            self._client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._client.ping()
            logger.info("qualis_cache_redis_connected", db=settings.cache_redis_db)
        except Exception as exc:
            logger.warning("qualis_cache_redis_unavailable", error=str(exc))
            self._client = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(self._full_key(key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("qualis_cache_get_failed", key=key, error=str(exc))
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            payload = json.dumps(value, default=str)
            full_key = self._full_key(key)
            if self._ttl > 0:
                self._client.setex(full_key, self._ttl, payload)
            else:
                self._client.set(full_key, payload)
        except Exception as exc:
            logger.warning("qualis_cache_set_failed", key=key, error=str(exc))

    def set_many(self, entries: dict[str, dict[str, Any]]) -> None:
        """Populate cache in a pipeline (seed warm-cache)."""
        if not self.enabled or not entries:
            return
        try:
            pipe = self._client.pipeline(transaction=False)
            for key, value in entries.items():
                payload = json.dumps(value, default=str)
                full_key = self._full_key(key)
                if self._ttl > 0:
                    pipe.setex(full_key, self._ttl, payload)
                else:
                    pipe.set(full_key, payload)
            pipe.execute()
        except Exception as exc:
            logger.warning("qualis_cache_set_many_failed", count=len(entries), error=str(exc))

    def invalidate_all(self) -> None:
        if not self.enabled:
            return
        try:
            pattern = self._full_key("qualis:*")
            for key in self._client.scan_iter(match=pattern, count=200):
                self._client.delete(key)
        except Exception as exc:
            logger.warning("qualis_cache_invalidate_failed", error=str(exc))


def qualis_cache_redis_url(redis_url: str, db: int) -> str:
    """Expose cache DB URL helper for scripts/tests."""
    return _cache_redis_url(redis_url, db)
