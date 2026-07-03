import uuid
from unittest.mock import MagicMock, patch

from apps.api.features.notifications.service import notification_service


@patch("apps.api.features.notifications.service.email_service")
@patch("apps.api.features.notifications.service.get_settings")
@patch("apps.api.features.notifications.service.evolution_service")
@patch("apps.api.features.notifications.service.logger")
def test_notify_run_completed_sends_email_when_whatsapp_opt_in_false(
    mock_logger, mock_evolution, mock_get_settings, mock_email
):
    mock_get_settings.return_value = MagicMock(
        whatsapp_notifications_enabled=True,
        app_display_name="Researchly",
        frontend_app_url="http://localhost:5173",
        app_env="production",
    )
    db = MagicMock()
    user = MagicMock()
    user.phone_number = "5582999999999"
    user.whatsapp_opt_in = False
    user.email = "user@example.com"
    db.query.return_value.filter_by.return_value.first.return_value = user

    run = MagicMock()
    run.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    run.id = "00000000-0000-0000-0000-000000000002"
    run.input = {"topics": ["AI in education"]}

    notification_service.notify_run_completed(db, run, recommendation_count=3)

    mock_evolution.send_text.assert_not_called()
    mock_email.send_text.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    assert kwargs["notification_type"] == "run_completed"


@patch("apps.api.features.notifications.service.get_settings")
@patch("apps.api.features.notifications.service.evolution_service")
@patch("apps.api.features.notifications.service.logger")
def test_notify_run_completed_sends_whatsapp_when_opted_in(mock_logger, mock_evolution, mock_get_settings):
    mock_get_settings.return_value = MagicMock(
        whatsapp_notifications_enabled=True,
        app_display_name="Researchly",
        frontend_app_url="http://localhost:5173",
    )
    mock_evolution.send_text.return_value = None
    db = MagicMock()
    user = MagicMock()
    user.phone_number = "5582999999999"
    user.whatsapp_opt_in = True
    user.email = "user@example.com"
    db.query.return_value.filter_by.return_value.first.return_value = user

    run = MagicMock()
    run.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    run.id = "00000000-0000-0000-0000-000000000002"
    run.input = {"topics": ["AI in education"]}

    notification_service.notify_run_completed(db, run, recommendation_count=3)

    mock_evolution.send_text.assert_called_once()
    mock_logger.info.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    assert kwargs["notification_type"] == "run_completed"
    assert "event" not in kwargs


@patch("apps.api.features.notifications.service.email_service")
@patch("apps.api.features.notifications.service.get_settings")
@patch("apps.api.features.notifications.service.evolution_service")
@patch("apps.api.features.notifications.service.logger")
def test_notify_run_completed_falls_back_to_email_when_whatsapp_fails(
    mock_logger, mock_evolution, mock_get_settings, mock_email
):
    from apps.api.features.auth.evolution import EvolutionError

    mock_get_settings.return_value = MagicMock(
        whatsapp_notifications_enabled=True,
        app_display_name="Researchly",
        frontend_app_url="http://localhost:5173",
        app_env="production",
    )
    mock_evolution.send_text.side_effect = EvolutionError("down")
    db = MagicMock()
    user = MagicMock()
    user.phone_number = "5582999999999"
    user.whatsapp_opt_in = True
    user.email = "user@example.com"
    db.query.return_value.filter_by.return_value.first.return_value = user

    run = MagicMock()
    run.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    run.id = "00000000-0000-0000-0000-000000000002"
    run.input = {"topics": ["AI in education"]}

    notification_service.notify_run_completed(db, run, recommendation_count=3)

    mock_email.send_text.assert_called_once()
    assert mock_logger.info.call_args[1]["notification_type"] == "run_completed"


@patch("apps.api.features.notifications.service.email_service")
@patch("apps.api.features.notifications.service.get_settings")
@patch("apps.api.features.notifications.service.logger")
def test_notify_run_failed_sends_email_when_no_whatsapp(mock_logger, mock_get_settings, mock_email):
    mock_get_settings.return_value = MagicMock(
        whatsapp_notifications_enabled=True,
        app_display_name="Researchly",
        frontend_app_url="http://localhost:5173",
        app_env="production",
    )
    db = MagicMock()
    user = MagicMock()
    user.phone_number = None
    user.whatsapp_opt_in = False
    user.email = "user@example.com"
    db.query.return_value.filter_by.return_value.first.return_value = user

    run = MagicMock()
    run.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    run.id = "00000000-0000-0000-0000-000000000002"

    notification_service.notify_run_failed(db, run, error_message="Timeout")

    mock_email.send_text.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    assert kwargs["notification_type"] == "run_failed"
