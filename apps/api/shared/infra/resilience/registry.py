"""Shared resilience singletons."""

from __future__ import annotations

from apps.api.shared.infra.resilience.circuit_breaker import SourceCircuitBreaker
from apps.api.shared.settings import get_settings

_circuit_breaker: SourceCircuitBreaker | None = None


def get_source_circuit_breaker() -> SourceCircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is not None:
        return _circuit_breaker

    settings = get_settings()
    redis_client = None
    if settings.redis_url:
        try:
            import redis

            redis_client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
            redis_client.ping()
        except Exception:
            redis_client = None

    _circuit_breaker = SourceCircuitBreaker(
        failure_threshold=settings.retrieval_circuit_failure_threshold,
        cooldown_seconds=settings.retrieval_circuit_cooldown_seconds,
        redis_client=redis_client,
        key_prefix=f"{settings.cache_key_prefix}:circuit",
    )
    return _circuit_breaker
