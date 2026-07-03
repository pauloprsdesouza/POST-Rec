"""Unit tests for OTP delivery channel selection (email-only OTP)."""

from unittest.mock import MagicMock, patch

import pytest

from apps.api.features.auth.service import AuthError, AuthService, auth_service


@pytest.fixture
def db() -> MagicMock:
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    session.query.return_value.filter.return_value.update.return_value = None
    session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
    session.query.return_value.filter_by.return_value.first.return_value = None
    return session


@pytest.fixture
def settings():
    settings = MagicMock(
        app_display_name="Researchly",
        app_env="production",
        jwt_secret="test-secret",
        otp_length=6,
        otp_ttl_minutes=5,
        otp_resend_seconds=60,
        otp_max_attempts=5,
    )
    with patch("apps.api.features.auth.service.get_settings", return_value=settings):
        yield settings


@patch("apps.api.features.auth.service.email_service")
def test_send_otp_uses_email_only(mock_email, db, settings):
    mock_email.is_configured.return_value = True

    service = AuthService()
    expires_in, dev_code, email_hint = service._send_otp(
        db,
        email="user@example.com",
        purpose="login",
    )

    mock_email.send_text.assert_called_once()
    assert dev_code is None
    assert email_hint == "u***@example.com"
    assert expires_in == 300


@patch("apps.api.features.auth.service.email_service")
def test_send_otp_email_required_in_production(mock_email, db, settings):
    from apps.api.features.auth.email import EmailError

    mock_email.send_text.side_effect = EmailError("SMTP down")
    mock_email.is_configured.return_value = True

    service = AuthService()
    with pytest.raises(AuthError, match="SMTP down"):
        service._send_otp(db, email="user@example.com", purpose="login")


@patch("apps.api.features.auth.service.auth_service._send_otp")
@patch("apps.api.features.auth.service.get_settings")
def test_register_without_phone_or_whatsapp(mock_get_settings, mock_send_otp, db):
    mock_get_settings.return_value = MagicMock(phone_default_country_code="55")
    mock_send_otp.return_value = (300, None, "u***@example.com")
    db.query.return_value.filter_by.return_value.first.return_value = None

    auth_service.register_and_request_otp(
        db,
        full_name="Jane Doe",
        email="user@example.com",
        phone_number=None,
        whatsapp_opt_in=False,
    )

    mock_send_otp.assert_called_once_with(db, email="user@example.com", purpose="register")


@patch("apps.api.features.auth.service.get_settings")
def test_register_rejects_whatsapp_without_phone(mock_get_settings, db):
    mock_get_settings.return_value = MagicMock(phone_default_country_code="55")
    db.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(AuthError, match="Add a WhatsApp number"):
        auth_service.register_and_request_otp(
            db,
            full_name="Jane Doe",
            email="user@example.com",
            phone_number=None,
            whatsapp_opt_in=True,
        )


@patch("apps.api.features.auth.service.auth_service._send_otp")
def test_request_login_otp_does_not_require_phone(mock_send_otp, db):
    user = MagicMock(email="user@example.com", phone_number=None, whatsapp_opt_in=False, is_active=True)
    db.query.return_value.filter_by.return_value.first.return_value = user
    mock_send_otp.return_value = (300, None, "u***@example.com")

    auth_service.request_login_otp(db, email="user@example.com")

    mock_send_otp.assert_called_once_with(db, email="user@example.com", purpose="login")


def test_update_account_rejects_whatsapp_opt_in_without_phone(db):
    user = MagicMock(
        full_name="Jane",
        email="user@example.com",
        phone_number=None,
        whatsapp_opt_in=False,
        id="00000000-0000-0000-0000-000000000001",
    )

    with pytest.raises(AuthError, match="Add a WhatsApp number"):
        auth_service.update_account(db, user, whatsapp_opt_in=True)


def test_update_account_clears_whatsapp_opt_in_when_phone_removed(db):
    user = MagicMock(
        full_name="Jane",
        email="user@example.com",
        phone_number="557999733237",
        whatsapp_opt_in=True,
        id="00000000-0000-0000-0000-000000000001",
    )

    auth_service.update_account(db, user, phone_number="   ")

    assert user.phone_number is None
    assert user.whatsapp_opt_in is False
    db.commit.assert_called_once()
