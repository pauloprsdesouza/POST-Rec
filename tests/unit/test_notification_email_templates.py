"""Unit tests for run notification email templates."""

from apps.api.features.notifications.email_templates import render_run_completed_email, render_run_failed_email


def test_render_run_completed_email():
    subject, plain, html = render_run_completed_email(
        app_name="Researchly",
        recommendation_count=5,
        topic_line="AI in education",
        app_url="http://localhost:5173",
        run_url="http://localhost:5173/runs/abc",
    )
    assert "ready" in subject.lower()
    assert "5 research ideas" in plain
    assert "AI in education" in plain
    assert "Review recommendations" in html
    assert "Run complete" in html


def test_render_run_failed_email():
    subject, plain, html = render_run_failed_email(
        app_name="Researchly",
        error_message="Pipeline timeout",
        app_url="http://localhost:5173",
        runs_url="http://localhost:5173/runs",
    )
    assert "could not be completed" in subject.lower()
    assert "Pipeline timeout" in plain
    assert "Try again" in html
    assert "Run failed" in html
