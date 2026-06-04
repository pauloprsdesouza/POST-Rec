"""Tests for HTTP retry helpers."""

from apps.api.services.http_retry import compute_backoff, parse_retry_after


class _FakeResponse:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


def test_compute_backoff_increases_with_attempt():
    first = compute_backoff(attempt=1, base_delay=2.0)
    third = compute_backoff(attempt=3, base_delay=2.0)
    assert third >= first


def test_compute_backoff_429_uses_longer_base():
    normal = compute_backoff(attempt=2, base_delay=2.0, status_code=500)
    throttled = compute_backoff(attempt=2, base_delay=2.0, status_code=429)
    assert throttled >= normal


def test_parse_retry_after_numeric_header():
    response = _FakeResponse({"Retry-After": "12"})
    assert parse_retry_after(response, attempt=0, base_delay=2.0) == 12.0
