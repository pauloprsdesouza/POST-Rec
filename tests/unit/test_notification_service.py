import uuid
from unittest.mock import MagicMock, patch

from apps.api.features.notifications.service import notification_service


@patch("apps.api.features.notifications.service.evolution_service")
@patch("apps.api.features.notifications.service.logger")
def test_notify_run_completed_logs_without_structlog_event_conflict(mock_logger, mock_evolution):
    mock_evolution.send_text.return_value = None
    db = MagicMock()
    user = MagicMock()
    user.phone_number = "5582999999999"
    user.whatsapp_opt_in = True
    db.query.return_value.filter_by.return_value.first.return_value = user

    run = MagicMock()
    run.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    run.id = "00000000-0000-0000-0000-000000000002"
    run.input = {"topics": ["AI in education"]}

    notification_service.notify_run_completed(db, run, recommendation_count=3)

    mock_logger.info.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    assert kwargs["notification_type"] == "run_completed"
    assert "event" not in kwargs
