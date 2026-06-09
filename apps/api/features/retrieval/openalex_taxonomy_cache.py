"""Redis-backed TTL cache layered on top of OpenAlex taxonomy loaders."""

from __future__ import annotations

import json
from typing import Callable

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.openalex_taxonomy_cache import cached_taxonomy_lookup

logger = get_logger("postrec-openalex-taxonomy-cache")


class OpenAlexTaxonomyRedisCache:
    def __init__(self) -> None:
        settings = get_settings()
        self._enabled = settings.retrieval_cache_enabled
        self._ttl = settings.retrieval_openalex_taxonomy_cache_ttl_seconds
        self._prefix = f"{settings.cache_key_prefix}:openalex:taxonomy"
        self._redis = None
        if self._enabled and settings.redis_url:
            try:
                import redis

                self._redis = redis.from_url(settings.redis_url, socket_connect_timeout=2)
                self._redis.ping()
            except Exception as exc:
                logger.warning("openalex_taxonomy_redis_unavailable", error=str(exc))
                self._redis = None

    def get_or_load(
        self,
        *,
        namespace: str,
        phrase: str,
        loader: Callable[[], tuple[str, ...]],
        extra: str = "",
    ) -> tuple[str, ...]:
        normalized = " ".join(phrase.lower().split())
        redis_key = f"{self._prefix}:{namespace}:{normalized}:{extra}"

        if self._redis:
            try:
                raw = self._redis.get(redis_key)
                if raw:
                    payload = json.loads(raw)
                    if isinstance(payload, list):
                        return tuple(str(item) for item in payload)
            except Exception as exc:
                logger.warning("openalex_taxonomy_redis_read_failed", error=str(exc))

        memory_key = f"{namespace}:{normalized}:{extra}"
        settings = get_settings()
        values = cached_taxonomy_lookup(
            memory_key,
            loader,
            ttl_seconds=settings.retrieval_openalex_taxonomy_cache_ttl_seconds,
        )

        if self._redis and values:
            try:
                self._redis.set(redis_key, json.dumps(list(values)), ex=self._ttl)
            except Exception as exc:
                logger.warning("openalex_taxonomy_redis_write_failed", error=str(exc))
        return values


_redis_cache: OpenAlexTaxonomyRedisCache | None = None


def get_openalex_taxonomy_redis_cache() -> OpenAlexTaxonomyRedisCache:
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = OpenAlexTaxonomyRedisCache()
    return _redis_cache
