"""Per-source circuit breaker for external API resilience."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from threading import Lock

from apps.api.shared.observability.logging import get_logger

logger = get_logger("postrec-resilience")


@dataclass(frozen=True)
class CircuitState:
    failures: int = 0
    open_until: float = 0.0
    last_status: int | None = None


class SourceCircuitOpenError(Exception):
    """Raised when a source circuit is open and requests should be skipped."""

    def __init__(self, source: str, *, retry_after_seconds: float):
        super().__init__(f"Circuit open for {source}")
        self.source = source
        self.retry_after_seconds = retry_after_seconds


class SourceCircuitBreaker:
    """AWS-style circuit breaker: fail fast after repeated 429/5xx."""

    def __init__(
        self,
        *,
        failure_threshold: int = 4,
        cooldown_seconds: float = 120.0,
        redis_client=None,
        key_prefix: str = "postrec:circuit",
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._local: dict[str, CircuitState] = {}
        self._lock = Lock()

    def _key(self, source: str) -> str:
        return f"{self._key_prefix}:{source}"

    def _load(self, source: str) -> CircuitState:
        if self._redis is not None:
            try:
                raw = self._redis.get(self._key(source))
                if raw:
                    payload = json.loads(raw)
                    return CircuitState(
                        failures=int(payload.get("failures", 0)),
                        open_until=float(payload.get("open_until", 0.0)),
                        last_status=payload.get("last_status"),
                    )
            except Exception as exc:
                logger.warning("circuit_breaker_redis_read_failed", source=source, error=str(exc))
        with self._lock:
            return self._local.get(source, CircuitState())

    def _save(self, source: str, state: CircuitState) -> None:
        if self._redis is not None:
            try:
                ttl = max(int(self.cooldown_seconds * 3), 300)
                self._redis.set(
                    self._key(source),
                    json.dumps(
                        {
                            "failures": state.failures,
                            "open_until": state.open_until,
                            "last_status": state.last_status,
                        }
                    ),
                    ex=ttl,
                )
                return
            except Exception as exc:
                logger.warning("circuit_breaker_redis_write_failed", source=source, error=str(exc))
        with self._lock:
            self._local[source] = state

    def seconds_until_closed(self, source: str) -> float:
        state = self._load(source)
        return max(0.0, state.open_until - time.time())

    def is_open(self, source: str) -> bool:
        return self.seconds_until_closed(source) > 0

    def allow_request(self, source: str) -> bool:
        return not self.is_open(source)

    def before_request(self, source: str) -> None:
        remaining = self.seconds_until_closed(source)
        if remaining > 0:
            raise SourceCircuitOpenError(source, retry_after_seconds=remaining)

    def record_success(self, source: str) -> None:
        self._save(source, CircuitState())

    def record_failure(self, source: str, *, status_code: int | None = None) -> None:
        state = self._load(source)
        failures = state.failures + 1
        open_until = state.open_until
        if failures >= self.failure_threshold:
            open_until = time.time() + self.cooldown_seconds
            logger.warning(
                "circuit_breaker_opened",
                source=source,
                failures=failures,
                cooldown_seconds=self.cooldown_seconds,
                status_code=status_code,
            )
            failures = 0
        self._save(
            source,
            CircuitState(failures=failures, open_until=open_until, last_status=status_code),
        )
