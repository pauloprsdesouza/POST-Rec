"""User-facing run activity log formatting."""

from __future__ import annotations

import re

from apps.api.shared.models import RecommendationRunEvent
from packages.postrec_core.domain.enums import RunStatus

_TERMINAL_FAILURE_STATUSES = frozenset(
    {
        RunStatus.FAILED,
        RunStatus.FAILED_SCHEMA_VALIDATION,
        RunStatus.COST_LIMIT_EXCEEDED,
    }
)

_FAILURE_EVENT_TYPES = frozenset(_TERMINAL_FAILURE_STATUSES)

_RECOVERY_HIDDEN_TYPES = frozenset(
    {
        RunStatus.FAILED,
        "retry_scheduled",
    }
)

_TECHNICAL_PATTERNS = (
    re.compile(r"'NoneType' object has no attribute", re.I),
    re.compile(r"\bNoneType\b.*\bget\b", re.I),
    re.compile(r"\bAttributeError\b", re.I),
    re.compile(r"object has no attribute", re.I),
    re.compile(r"RetryableFetchError", re.I),
    re.compile(r"HTTPStatusError", re.I),
    re.compile(r"^\s*Failed:\s*", re.I),
    re.compile(r"\bTraceback\b", re.I),
)

_TEMPORARY_ERROR_MESSAGE = "A temporary error occurred while processing this run."


def is_technical_message(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _TECHNICAL_PATTERNS)


def sanitize_error_for_user(error: str) -> str:
    text = (error or "").strip()
    if not text:
        return "The run could not be completed."
    if text.lower().startswith("failed:"):
        text = text[7:].strip()
    if is_technical_message(text):
        return _TEMPORARY_ERROR_MESSAGE
    if len(text) > 240:
        return text[:237] + "…"
    return text


def sanitize_run_error_message(error: str | None) -> str | None:
    if not error:
        return None
    sanitized = sanitize_error_for_user(error)
    return sanitized or None


def retry_user_message(exc: Exception) -> str:
    text = str(exc)
    if "NoneType" in text and "get" in text:
        return "A source returned unexpected data — retrying automatically…"
    if "429" in text or "rate limit" in text.lower():
        return "Sources are rate-limited — retrying in a moment…"
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "A source timed out — retrying automatically…"
    return "A temporary error occurred — retrying automatically…"


def failure_user_message(exc: Exception) -> str:
    return sanitize_error_for_user(str(exc))


def _event_level(event_type: str, message: str) -> str:
    if event_type in _FAILURE_EVENT_TYPES:
        return "error"
    if event_type in ("retry_scheduled", "source_retry"):
        return "warning"
    if message.lower().startswith("failed:") or is_technical_message(message):
        return "error"
    return "info"


def _public_message(event_type: str, message: str) -> str:
    if event_type == "retry_scheduled":
        return retry_user_message(Exception(message)) if is_technical_message(message) else message
    if is_technical_message(message):
        return sanitize_error_for_user(message)
    if event_type == RunStatus.FAILED and message.lower().startswith("failed:"):
        return sanitize_error_for_user(message[7:].strip())
    return message


def _should_hide_event(run_status: str, event_type: str, message: str) -> bool:
    """Hide superseded failure/retry noise unless the run truly failed."""
    run_failed = run_status in _TERMINAL_FAILURE_STATUSES
    hide_failure_noise = not run_failed

    if hide_failure_noise and event_type in _FAILURE_EVENT_TYPES:
        return True
    if hide_failure_noise and event_type == "retry_scheduled":
        return True
    if hide_failure_noise and message.lower().startswith("failed:"):
        return True
    if hide_failure_noise and is_technical_message(message):
        return True

    public_message = _public_message(event_type, message)
    if hide_failure_noise and public_message == _TEMPORARY_ERROR_MESSAGE:
        return True

    if run_status == RunStatus.COMPLETED and event_type in _RECOVERY_HIDDEN_TYPES:
        return True

    return False


def format_events_for_user(
    events: list[RecommendationRunEvent],
    run_status: str,
) -> list[dict]:
    """Drop superseded failure/retry noise when the run is active or ultimately succeeded."""
    formatted: list[dict] = []

    for event in events:
        event_type = event.event_type or ""
        message = event.message or ""

        if _should_hide_event(run_status, event_type, message):
            continue

        public_message = _public_message(event_type, message)
        if is_technical_message(public_message):
            continue

        formatted.append(
            {
                "id": str(event.id),
                "event_type": event_type,
                "message": public_message,
                "created_at": event.created_at,
                "level": _event_level(event_type, message),
            }
        )

    return formatted
