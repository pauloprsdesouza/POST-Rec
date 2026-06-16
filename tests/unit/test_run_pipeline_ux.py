"""Tests for run pipeline UX helpers."""

from unittest.mock import MagicMock

import pytest

from apps.api.workers.tasks import _report_substep


@pytest.fixture
def mock_run_services(monkeypatch):
    events = []
    bumps = []

    def fake_add_event(db, run, event_type, message, payload=None):
        events.append((event_type, message))

    def fake_bump(db, run, progress):
        bumps.append(progress)

    monkeypatch.setattr("apps.api.workers.tasks.run_service._add_event", fake_add_event)
    monkeypatch.setattr("apps.api.workers.tasks.run_service.bump_progress", fake_bump)
    monkeypatch.setattr("apps.api.workers.tasks._invalidate_run_caches", lambda run: None)
    monkeypatch.setattr("apps.api.workers.tasks.run_stream_service.publish", lambda db, run: None)

    db = MagicMock()
    run = MagicMock()
    return db, run, events, bumps


def test_report_substep_publishes_event_and_progress(mock_run_services):
    db, run, events, bumps = mock_run_services

    _report_substep(db, run, "Scoring papers for relevance", 28)

    assert events == [("pipeline_progress", "Scoring papers for relevance")]
    assert bumps == [28]
    db.commit.assert_called_once()
