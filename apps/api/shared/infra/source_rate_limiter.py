"""Per-source request pacing to respect external API limits."""

import asyncio
import time
from threading import Lock

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-retrieval")

# Conservative defaults (Semantic Scholar / arXiv are strictest).
DEFAULT_SOURCE_MIN_INTERVAL_SECONDS = {
    "openalex": 0.35,
    "crossref": 0.35,
    "semantic_scholar": 5.0,
    "arxiv": 4.0,
}


class SourceRateLimiter:
    """Redis-backed limiter with in-process fallback."""

    def __init__(self) -> None:
        self._local_last_request: dict[str, float] = {}
        self._local_lock = Lock()
        self._redis = None
        settings = get_settings()
        if settings.redis_url:
            try:
                import redis

                self._redis = redis.from_url(settings.redis_url, socket_connect_timeout=2)
                self._redis.ping()
            except Exception as exc:
                logger.warning("rate_limiter_redis_unavailable", error=str(exc))
                self._redis = None

    def _interval(self, source: str) -> float:
        settings = get_settings()
        configured = {
            "openalex": settings.retrieval_openalex_min_interval,
            "crossref": settings.retrieval_crossref_min_interval,
            "semantic_scholar": settings.retrieval_semantic_scholar_min_interval,
            "arxiv": settings.retrieval_arxiv_min_interval,
        }
        return configured.get(source, DEFAULT_SOURCE_MIN_INTERVAL_SECONDS.get(source, 0.5))

    def _wait_local(self, source: str) -> float:
        interval = self._interval(source)
        with self._local_lock:
            now = time.monotonic()
            last = self._local_last_request.get(source, 0.0)
            wait = interval - (now - last)
            if wait > 0:
                time.sleep(wait)
            self._local_last_request[source] = time.monotonic()
        return max(wait, 0.0)

    def _wait_redis(self, source: str) -> float:
        assert self._redis is not None
        interval = self._interval(source)
        key = f"{get_settings().cache_key_prefix}:ratelimit:{source}"
        while True:
            now = time.time()
            raw = self._redis.get(key)
            if raw:
                elapsed = now - float(raw)
                if elapsed < interval:
                    time.sleep(interval - elapsed)
            self._redis.set(key, str(time.time()), ex=max(int(interval * 4), 10))
            return 0.0

    def wait(self, source: str) -> None:
        if self._redis is not None:
            try:
                self._wait_redis(source)
                return
            except Exception as exc:
                logger.warning("rate_limiter_redis_failed", source=source, error=str(exc))
        self._wait_local(source)

    async def wait_async(self, source: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.wait, source)


source_rate_limiter = SourceRateLimiter()
