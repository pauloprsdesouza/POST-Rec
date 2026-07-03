"""Operational metrics — Prometheus scrape + OTLP export when enabled."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

if TYPE_CHECKING:
    from opentelemetry.metrics import Counter as OtelCounter
    from opentelemetry.metrics import Histogram as OtelHistogram

_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)

http_requests_total = Counter(
    "postrec_http_requests_total",
    "Total HTTP requests processed by the API",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "postrec_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

_celery_tasks_total: Counter | None = None

_otel_http_counter: OtelCounter | None = None
_otel_http_duration: OtelHistogram | None = None
_otel_celery_counter: OtelCounter | None = None
_otel_ready = False


def _ensure_otel_instruments() -> None:
    global _otel_http_counter, _otel_http_duration, _otel_celery_counter, _otel_ready
    if _otel_ready:
        return

    from apps.api.shared.settings import get_settings

    if not get_settings().otel_enabled:
        _otel_ready = True
        return

    from opentelemetry import metrics

    meter = metrics.get_meter("postrec")
    _otel_http_counter = meter.create_counter(
        "postrec.http.requests.total",
        description="Total HTTP requests processed by the API",
        unit="1",
    )
    _otel_http_duration = meter.create_histogram(
        "postrec.http.request.duration.seconds",
        description="HTTP request duration in seconds",
        unit="s",
    )
    _otel_celery_counter = meter.create_counter(
        "postrec.celery.tasks.total",
        description="Total Celery tasks processed",
        unit="1",
    )
    _otel_ready = True


def normalize_endpoint(path: str) -> str:
    """Collapse UUID path segments to keep Prometheus cardinality bounded."""
    return _UUID_PATTERN.sub("{id}", path)


def record_http_request(*, method: str, endpoint: str, status: str, duration_seconds: float) -> None:
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_seconds)

    _ensure_otel_instruments()
    if _otel_http_counter is not None:
        attrs = {"http.method": method, "http.route": endpoint, "http.status_code": status}
        _otel_http_counter.add(1, attrs)
    if _otel_http_duration is not None:
        _otel_http_duration.record(
            duration_seconds,
            {"http.method": method, "http.route": endpoint, "http.status_code": status},
        )


def _get_celery_tasks_total() -> Counter:
    """Create the counter lazily so prefork workers register metrics after fork."""
    global _celery_tasks_total
    if _celery_tasks_total is None:
        _celery_tasks_total = Counter(
            "postrec_celery_tasks_total",
            "Total Celery tasks processed",
            ["task", "state"],
        )
    return _celery_tasks_total


def record_celery_task(*, task: str, state: str) -> None:
    _get_celery_tasks_total().labels(task=task, state=state).inc()

    _ensure_otel_instruments()
    if _otel_celery_counter is not None:
        _otel_celery_counter.add(1, {"celery.task": task, "celery.state": state})


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
