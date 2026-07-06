"""Redis cache for historical and slow-changing read paths."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse, urlunparse

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.domain.enums import RunStatus

logger = get_logger("postrec-cache")

TERMINAL_RUN_STATUSES = frozenset(
    {
        RunStatus.COMPLETED,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
        RunStatus.COST_LIMIT_EXCEEDED,
        RunStatus.FAILED_SCHEMA_VALIDATION,
    }
)


class CacheTTL:
    """Strategic TTLs — historical/immutable data gets longer TTLs."""

    CONSENT = 86_400  # 24h — accepted once, rarely changes
    ACCOUNT = 900  # 15min — semi-static user fields
    PROFILE = 600  # 10min — slowly changing (feedback merges topics)
    RUNS_LIST = 60  # 1min — status/progress can change while runs are active
    RUN_ACTIVE = 3  # 3s — matches 5s frontend polling without stale UI
    RUN_TERMINAL = 86_400  # 24h — finished runs are historical
    RUN_EVENTS_ACTIVE = 5  # 5s — append-only while running
    RUN_EVENTS_TERMINAL = 86_400  # 24h — immutable after completion
    RECOMMENDATIONS = 604_800  # 7d — frozen after run completes
    SOURCE_DOCUMENTS = 604_800  # 7d — paper metadata is stable
    VALIDATION_DASHBOARD = 600  # 10min — aggregate metrics, expensive to compute
    RESEARCH_REPORT = 600  # 10min — full statistical report
    ADMIN_OVERVIEW = 60  # 1min — operator dashboard aggregates


class CacheKeys:
    @staticmethod
    def user_consent(user_id: str) -> str:
        return f"user:{user_id}:consent"

    @staticmethod
    def user_account(user_id: str) -> str:
        return f"user:{user_id}:account"

    @staticmethod
    def user_profile(user_id: str) -> str:
        return f"user:{user_id}:profile"

    @staticmethod
    def user_runs(user_id: str, limit: int) -> str:
        return f"user:{user_id}:runs:{limit}"

    @staticmethod
    def run_detail(run_id: str) -> str:
        return f"run:{run_id}:detail"

    @staticmethod
    def run_events(run_id: str) -> str:
        return f"run:{run_id}:events"

    @staticmethod
    def run_recommendations(run_id: str) -> str:
        return f"run:{run_id}:recommendations"

    @staticmethod
    def run_sources(run_id: str) -> str:
        return f"run:{run_id}:sources"

    @staticmethod
    def validation_dashboard() -> str:
        return "validation:dashboard"

    @staticmethod
    def research_report() -> str:
        return "validation:research_report"

    @staticmethod
    def admin_overview() -> str:
        return "admin:overview"


def run_detail_ttl(status: str) -> int:
    return CacheTTL.RUN_TERMINAL if status in TERMINAL_RUN_STATUSES else CacheTTL.RUN_ACTIVE


def run_events_ttl(status: str) -> int:
    return CacheTTL.RUN_EVENTS_TERMINAL if status in TERMINAL_RUN_STATUSES else CacheTTL.RUN_EVENTS_ACTIVE


def is_terminal_run(status: str) -> bool:
    return status in TERMINAL_RUN_STATUSES


class CacheService:
    """JSON cache-aside on a dedicated Redis DB (default DB 2)."""

    def __init__(self) -> None:
        self._client = None
        self._enabled = False
        self._prefix = ""
        self._configure()

    def _configure(self) -> None:
        settings = get_settings()
        self._prefix = settings.cache_key_prefix
        self._enabled = settings.cache_enabled and bool(settings.redis_url)
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
            logger.info("cache_redis_connected", db=settings.cache_redis_db)
        except Exception as exc:
            logger.warning("cache_redis_unavailable", error=str(exc))
            self._client = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get_json(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(self._full_key(key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("cache_get_failed", key=key, error=str(exc))
            return None

    def set_json(self, key: str, value: Any, ttl: int) -> None:
        if not self.enabled:
            return
        try:
            payload = json.dumps(value, default=str)
            self._client.setex(self._full_key(key), ttl, payload)
        except Exception as exc:
            logger.warning("cache_set_failed", key=key, error=str(exc))

    def delete(self, *keys: str) -> None:
        if not self.enabled or not keys:
            return
        try:
            self._client.delete(*[self._full_key(key) for key in keys])
        except Exception as exc:
            logger.warning("cache_delete_failed", keys=list(keys), error=str(exc))

    def delete_pattern(self, pattern: str) -> None:
        if not self.enabled:
            return
        try:
            full_pattern = self._full_key(pattern)
            for key in self._client.scan_iter(match=full_pattern, count=100):
                self._client.delete(key)
        except Exception as exc:
            logger.warning("cache_delete_pattern_failed", pattern=pattern, error=str(exc))

    def get_or_load(self, key: str, ttl: int, loader: Callable[[], Any]) -> Any:
        cached = self.get_json(key)
        if cached is not None:
            return cached
        value = loader()
        if value is not None:
            self.set_json(key, value, ttl)
        return value

    def invalidate_user(self, user_id: str) -> None:
        self.delete_pattern(f"user:{user_id}:*")

    def invalidate_user_profile(self, user_id: str) -> None:
        self.delete(CacheKeys.user_profile(user_id))

    def invalidate_user_consent(self, user_id: str) -> None:
        self.delete(CacheKeys.user_consent(user_id))

    def invalidate_user_account(self, user_id: str) -> None:
        self.delete(CacheKeys.user_account(user_id))

    def invalidate_user_runs(self, user_id: str) -> None:
        self.delete_pattern(f"user:{user_id}:runs:*")

    def invalidate_run(self, run_id: str) -> None:
        self.delete(
            CacheKeys.run_detail(run_id),
            CacheKeys.run_events(run_id),
            CacheKeys.run_recommendations(run_id),
            f"{CacheKeys.run_recommendations(run_id)}:published",
            f"{CacheKeys.run_recommendations(run_id)}:all",
            CacheKeys.run_sources(run_id),
        )

    def invalidate_validation_dashboard(self) -> None:
        self.delete(CacheKeys.validation_dashboard(), CacheKeys.research_report())


def _cache_redis_url(redis_url: str, db: int) -> str:
    parsed = urlparse(redis_url)
    path = f"/{db}"
    return urlunparse(parsed._replace(path=path))


cache_service = CacheService()
