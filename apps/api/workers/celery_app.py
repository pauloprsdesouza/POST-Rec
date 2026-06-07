"""Celery application configuration."""

import sys

from celery import Celery
from celery.signals import worker_process_init
from kombu import Exchange, Queue

from apps.api.observability.logging import configure_logging, get_logger
from apps.api.services.embedding_config import validate_embedding_configuration
from apps.api.settings import get_settings

configure_logging()
logger = get_logger("postrec-celery")

settings = get_settings()


@worker_process_init.connect
def validate_worker_embedding_configuration(**_kwargs) -> None:
    current = get_settings()
    validate_embedding_configuration(current.gemini_embedding_model)
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
        "postrec.recommendation.embedding",
        "postrec.recommendation.ranking",
        "postrec.recommendation.llm",
        "postrec.recommendation.export",
        "postrec.validation.metrics",
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
        "apps.api.workers.tasks.generate_embeddings_task": {"queue": "postrec.recommendation.embedding"},
        "apps.api.workers.tasks.generate_recommendations_task": {"queue": "postrec.recommendation.llm"},
    },
)
