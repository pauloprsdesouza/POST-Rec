"""Celery application configuration."""

import sys

from celery import Celery
from celery.signals import celeryd_init, worker_process_init, worker_ready
from kombu import Exchange, Queue

from apps.api.shared.infra.embedding_config import validate_embedding_configuration
from apps.api.shared.observability.logging import configure_logging, get_logger
from apps.api.shared.settings import get_settings

configure_logging()
logger = get_logger("postrec-celery")

settings = get_settings()


@celeryd_init.connect
def init_prometheus_multiprocess(**_kwargs) -> None:
    from apps.api.shared.observability.worker_metrics import prepare_multiprocess_dir

    prepare_multiprocess_dir()


@worker_ready.connect
def launch_worker_metrics_server(**_kwargs) -> None:
    from apps.api.shared.observability.worker_metrics import start_worker_metrics_server

    start_worker_metrics_server(port=9101)


@worker_process_init.connect
def validate_worker_embedding_configuration(**_kwargs) -> None:
    current = get_settings()
    validate_embedding_configuration(current.gemini_embedding_model)
    from apps.api.shared.observability.telemetry import setup_observability

    setup_observability(service_name=f"{current.otel_service_name}-worker")
    # Import after fork so prometheus_client counters are created in worker children.
    import apps.api.shared.observability.celery_metrics  # noqa: E402, F401

    logger.info("worker_embedding_model_validated", model=current.gemini_embedding_model)

celery_app = Celery(
    "postrec",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["apps.api.workers.tasks"],
)

POSTREC_EXCHANGE = Exchange("postrec.recommendation", type="direct")

# RabbitMQ 4: use durable classic queues (compatible with homelab stack).
TASK_QUEUES = tuple(
    Queue(
        name,
        exchange=POSTREC_EXCHANGE,
        routing_key=name,
        durable=True,
    )
    for name in (
        "postrec.recommendation.default",
        "postrec.recommendation.retrieval",
    )
)

worker_pool = "solo" if sys.platform == "win32" else "prefork"

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=900,
    task_soft_time_limit=840,
    broker_connection_retry_on_startup=True,
    task_default_queue="postrec.recommendation.default",
    task_queues=TASK_QUEUES,
    worker_pool=worker_pool,
    worker_concurrency=1 if sys.platform == "win32" else None,
    worker_disable_mingle=True,
    task_create_missing_queues=True,
    task_routes={
        "apps.api.workers.tasks.process_recommendation_run": {"queue": "postrec.recommendation.default"},
        "apps.api.workers.tasks.deferred_source_fetch": {"queue": "postrec.recommendation.retrieval"},
    },
)
