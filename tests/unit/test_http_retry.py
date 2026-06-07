"""Tests for HTTP retry helpers."""

from apps.api.services.http_retry import compute_backoff, full_jitter_backoff, parse_retry_after


class _FakeResponse:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


def test_compute_backoff_ceiling_grows_with_attempt():
    """Full jitter is random; verify the upper bound increases with attempt."""
    samples = {attempt: [compute_backoff(attempt=attempt, base_delay=2.0) for _ in range(40)] for attempt in (1, 2, 3)}
    assert max(samples[3]) > max(samples[1])
    for attempt, values in samples.items():
        ceiling = min(2.0 * (2 ** max(attempt - 1, 0)), 120.0)
        assert all(0.0 <= value <= ceiling for value in values)


def test_compute_backoff_429_uses_higher_ceiling():
    """429 responses use a larger backoff cap than other retryable errors."""
    normal = [compute_backoff(attempt=2, base_delay=2.0, status_code=500) for _ in range(40)]
    throttled = [compute_backoff(attempt=2, base_delay=2.0, status_code=429) for _ in range(40)]
    assert max(throttled) > max(normal)
    assert all(value <= 4.0 for value in normal)
    assert all(value <= 10.0 for value in throttled)


def test_full_jitter_backoff_bounded():
    for _ in range(20):
        value = full_jitter_backoff(attempt=3, base_delay=2.0, max_delay=60.0, status_code=429)
        assert 0.0 <= value <= 90.0


def test_parse_retry_after_numeric_header():
    response = _FakeResponse({"Retry-After": "12"})
    assert parse_retry_after(response, attempt=0, base_delay=2.0) == 12.0
