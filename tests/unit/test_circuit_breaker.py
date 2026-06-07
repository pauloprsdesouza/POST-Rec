"""Tests for source circuit breaker."""

from apps.api.services.resilience.circuit_breaker import SourceCircuitBreaker


def test_circuit_opens_after_threshold():
    breaker = SourceCircuitBreaker(failure_threshold=3, cooldown_seconds=30.0)
    for _ in range(3):
        breaker.record_failure("semantic_scholar", status_code=429)
    assert breaker.is_open("semantic_scholar")


def test_circuit_recovers_after_success():
    breaker = SourceCircuitBreaker(failure_threshold=2, cooldown_seconds=60.0)
    breaker.record_failure("arxiv", status_code=429)
    breaker.record_failure("arxiv", status_code=429)
    assert breaker.is_open("arxiv")
    breaker.record_success("arxiv")
    assert not breaker.is_open("arxiv")


def test_circuit_open_has_retry_window():
    breaker = SourceCircuitBreaker(failure_threshold=1, cooldown_seconds=10.0)
    breaker.record_failure("crossref", status_code=429)
    remaining = breaker.seconds_until_closed("crossref")
    assert 0 < remaining <= 10.0
