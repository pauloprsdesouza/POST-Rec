"""Celery task lifecycle metrics via signals."""

from __future__ import annotations

from celery.signals import task_failure, task_retry, task_success

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.observability.metrics import record_celery_task

logger = get_logger("postrec-celery-metrics")


def _short_task_name(sender) -> str:
    name = getattr(sender, "name", None) or "unknown"
    return str(name).rsplit(".", 1)[-1]


@task_success.connect
def on_task_success(sender=None, **kwargs) -> None:
    task = _short_task_name(sender)
    record_celery_task(task=task, state="success")
    logger.debug("celery_task_metric", task=task, state="success")


@task_failure.connect
def on_task_failure(sender=None, **kwargs) -> None:
    task = _short_task_name(sender)
    record_celery_task(task=task, state="failure")
    logger.debug("celery_task_metric", task=task, state="failure")


@task_retry.connect
def on_task_retry(sender=None, **kwargs) -> None:
    task = _short_task_name(sender)
    record_celery_task(task=task, state="retry")
    logger.debug("celery_task_metric", task=task, state="retry")
