"""Tests for run progress updates."""

from unittest.mock import MagicMock, patch

from apps.api.features.runs.service import run_service


@patch("apps.api.features.runs.service.run_stream_service")
@patch("apps.api.features.runs.service.cache_service")
def test_bump_progress_raises_and_publishes(mock_cache, mock_stream):
    db = MagicMock()
    run = MagicMock()
    run.progress = 15
    run.user_id = None

    run_service.bump_progress(db, run, 30)

    assert run.progress == 30
    db.commit.assert_called_once()
    mock_cache.invalidate_run.assert_called_once()
    mock_stream.publish.assert_called_once_with(db, run)


@patch("apps.api.features.runs.service.run_stream_service")
@patch("apps.api.features.runs.service.cache_service")
def test_bump_progress_skips_when_not_higher(mock_cache, mock_stream):
    db = MagicMock()
    run = MagicMock()
    run.progress = 45

    run_service.bump_progress(db, run, 30)

    db.commit.assert_not_called()
    mock_stream.publish.assert_not_called()
