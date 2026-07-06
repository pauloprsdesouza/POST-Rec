"""OpenTelemetry traces, logs, and metrics export."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger("postrec-telemetry")

_instrumented = False


def _grpc_endpoint(raw: str) -> tuple[str, bool]:
    """Return (host:port, insecure) for OTLP gRPC exporters."""
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    host = parsed.hostname or "localhost"
    port = parsed.port or 4317
    insecure = parsed.scheme != "https"
    return f"{host}:{port}", insecure


def _build_resource(service_name: str):
    from opentelemetry.sdk.resources import Resource

    settings = get_settings()
    return Resource.create(
        {
            "service.name": service_name,
            "service.namespace": "post-rec",
            "deployment.environment": settings.app_env,
        }
    )


def _setup_traces(resource, endpoint: str, insecure: bool, app: FastAPI | None) -> None:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=insecure)))
    trace.set_tracer_provider(provider)

    if app is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    from apps.api.shared.database import engine

    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()


def _setup_logs(resource, endpoint: str, insecure: bool) -> None:
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=insecure))
    )
    set_logger_provider(log_provider)

    otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)
    root = logging.getLogger()
    if not any(isinstance(h, LoggingHandler) for h in root.handlers):
        root.addHandler(otel_handler)


def _setup_metrics(resource, endpoint: str, insecure: bool) -> None:
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=insecure),
        export_interval_millis=15_000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))


def setup_observability(*, service_name: str | None = None, app: FastAPI | None = None) -> None:
    """Configure OTLP traces, logs, and metrics when enabled in settings."""
    global _instrumented
    settings = get_settings()
    if not settings.otel_enabled:
        return
    if _instrumented:
        return

    name = service_name or settings.otel_service_name
    endpoint, insecure = _grpc_endpoint(settings.otel_exporter_otlp_endpoint)
    resource = _build_resource(name)

    _setup_traces(resource, endpoint, insecure, app)
    _setup_logs(resource, endpoint, insecure)
    _setup_metrics(resource, endpoint, insecure)

    _instrumented = True
    logger.info(
        "otel_observability_enabled",
        service=name,
        endpoint=settings.otel_exporter_otlp_endpoint,
        grpc_endpoint=endpoint,
    )


# Backward-compatible alias
def setup_tracing(*, service_name: str | None = None, app: FastAPI | None = None) -> None:
    setup_observability(service_name=service_name, app=app)
