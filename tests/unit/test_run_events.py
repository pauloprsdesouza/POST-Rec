"""Tests for user-facing run event formatting."""

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.shared.models import RecommendationRunEvent
from apps.api.features.runs.events import (
    format_events_for_user,
    retry_user_message,
    sanitize_error_for_user,
    sanitize_run_error_message,
)
from packages.postrec_core.domain.enums import RunStatus


def _event(event_type: str, message: str) -> RecommendationRunEvent:

    return RecommendationRunEvent(
        id=uuid4(),
        run_id=uuid4(),
        session_id=uuid4(),
        event_type=event_type,
        message=message,
        created_at=datetime.now(UTC),
    )


def test_hide_failed_events_when_run_completed():

    events = [
        _event(RunStatus.SEARCHING_PAPERS, "Searching papers"),
        _event(RunStatus.FAILED, "Failed: 'NoneType' object has no attribute 'get'"),
        _event(RunStatus.COMPLETED, "Run completed"),
    ]

    visible = format_events_for_user(events, RunStatus.COMPLETED)

    messages = [item["message"] for item in visible]

    assert "Failed:" not in " ".join(messages)

    assert "temporary error" not in " ".join(messages).lower()

    assert "NoneType" not in " ".join(messages)

    assert any("Searching papers" in message for message in messages)

    assert any("Run completed" in message for message in messages)


def test_hide_failed_events_while_run_in_progress():

    events = [
        _event(RunStatus.SEARCHING_PAPERS, "Searching papers"),
        _event(
            RunStatus.FAILED,
            "A temporary error occurred while processing this run.",
        ),
    ]

    visible = format_events_for_user(events, RunStatus.SEARCHING_PAPERS)

    messages = [item["message"] for item in visible]

    assert messages == ["Searching papers"]


def test_sanitize_raw_failed_event_without_prefix():

    events = [
        _event(
            RunStatus.FAILED,
            "AttributeError: 'NoneType' object has no attribute 'get'",
        ),
    ]

    visible = format_events_for_user(events, RunStatus.FAILED)

    assert len(visible) == 1

    assert "NoneType" not in visible[0]["message"]

    assert "temporary error" in visible[0]["message"].lower()


def test_hide_raw_technical_message_on_any_event_type():

    events = [
        _event("searching_papers", "AttributeError: 'NoneType' object has no attribute 'get'"),
        _event(RunStatus.SEARCHING_PAPERS, "Searching papers"),
    ]

    visible = format_events_for_user(events, RunStatus.SEARCHING_PAPERS)

    messages = [item["message"] for item in visible]

    assert messages == ["Searching papers"]


def test_show_failed_events_when_run_failed():

    events = [
        _event(RunStatus.SEARCHING_PAPERS, "Searching papers"),
        _event(RunStatus.FAILED, "Failed: 'NoneType' object has no attribute 'get'"),
    ]

    visible = format_events_for_user(events, RunStatus.FAILED)

    messages = [item["message"] for item in visible]

    assert any("temporary error" in message.lower() for message in messages)

    assert all("NoneType" not in message for message in messages)


def test_retry_message_is_user_friendly():

    message = retry_user_message(AttributeError("'NoneType' object has no attribute 'get'"))

    assert "NoneType" not in message

    assert "retry" in message.lower()


def test_sanitize_technical_error():

    sanitized = sanitize_error_for_user("Failed: 'NoneType' object has no attribute 'get'")

    assert "NoneType" not in sanitized


def test_sanitize_run_error_message():

    assert sanitize_run_error_message("'NoneType' object has no attribute 'get'") is not None

    assert "NoneType" not in sanitize_run_error_message("'NoneType' object has no attribute 'get'")
