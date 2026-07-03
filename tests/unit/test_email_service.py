"""Unit tests for SMTP email service."""

from unittest.mock import MagicMock, patch

import pytest

from apps.api.features.auth.email import EmailError, EmailService


@patch("apps.api.features.auth.email.get_settings")
def test_is_configured_requires_host_and_from(mock_get_settings):
    mock_get_settings.return_value = MagicMock(smtp_host="smtp.example.com", email_from="noreply@example.com")
    service = EmailService()
    assert service.is_configured() is True

    mock_get_settings.return_value = MagicMock(smtp_host="", email_from="noreply@example.com")
    assert EmailService().is_configured() is False


@patch("apps.api.features.auth.email.get_settings")
@patch("apps.api.features.auth.email.logger")
def test_send_text_mocks_in_development_when_unconfigured(mock_logger, mock_get_settings):
    mock_get_settings.return_value = MagicMock(
        smtp_host="",
        email_from="noreply@example.com",
        app_env="development",
    )
    service = EmailService()
    service.send_text("user@example.com", "Subject", "Body")
    mock_logger.warning.assert_called_once()


@patch("apps.api.features.auth.email.get_settings")
def test_send_text_raises_in_production_when_unconfigured(mock_get_settings):
    mock_get_settings.return_value = MagicMock(
        smtp_host="",
        email_from="noreply@example.com",
        app_env="production",
    )
    service = EmailService()
    with pytest.raises(EmailError, match="Email is not configured"):
        service.send_text("user@example.com", "Subject", "Body")


@patch("apps.api.features.auth.email.smtplib.SMTP")
@patch("apps.api.features.auth.email.get_settings")
def test_send_text_uses_smtp(mock_get_settings, mock_smtp):
    settings = MagicMock(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="secret",
        smtp_use_tls=True,
        email_from="noreply@paulorobertosouza.com.br",
        email_from_name="",
        app_display_name="Researchly",
        app_env="production",
    )
    mock_get_settings.return_value = settings
    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server

    EmailService().send_text("user@example.com", "Sign-in code", "Your code is 123456")

    mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "secret")
    server.send_message.assert_called_once()
