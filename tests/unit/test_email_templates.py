"""Unit tests for OTP email templates."""

from apps.api.features.auth.email_templates import render_otp_email


def test_render_otp_email_plain_text():
    plain, _html = render_otp_email(app_name="Researchly", code="123456", ttl_minutes=5, purpose="login")
    assert "Researchly sign-in code: 123456." in plain
    assert "Valid for 5 minutes" in plain
    assert "safely ignore" in plain


def test_render_otp_email_html_contains_branded_layout():
    _plain, html = render_otp_email(
        app_name="Researchly",
        code="654321",
        ttl_minutes=10,
        purpose="register",
    )
    assert "Researchly" in html
    assert "654321" in html
    assert "complete your registration" in html
    assert "10 minutes" in html
    assert "#4338ca" in html
    assert "<!DOCTYPE html>" in html


def test_render_otp_email_escapes_html_in_app_name():
    _plain, html = render_otp_email(app_name="<Evil>", code="111111", ttl_minutes=5)
    assert "&lt;Evil&gt;" in html
    assert "<Evil>" not in html
