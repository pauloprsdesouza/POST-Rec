"""Redis cache service tests."""

from unittest.mock import MagicMock

from apps.api.services.cache_service import (
    CacheKeys,
    CacheTTL,
    CacheService,
    _cache_redis_url,
    is_terminal_run,
    run_detail_ttl,
    run_events_ttl,
)
from packages.postrec_core.domain.enums import RunStatus


def test_cache_redis_url_switches_db():
    url = _cache_redis_url("redis://:secret@192.168.1.1:6379/0", 2)
    assert url == "redis://:secret@192.168.1.1:6379/2"


def test_run_ttl_terminal_vs_active():
    assert run_detail_ttl(RunStatus.COMPLETED) == CacheTTL.RUN_TERMINAL
    assert run_detail_ttl(RunStatus.SEARCHING_PAPERS) == CacheTTL.RUN_ACTIVE
    assert run_events_ttl(RunStatus.FAILED) == CacheTTL.RUN_EVENTS_TERMINAL
    assert run_events_ttl(RunStatus.GENERATING_RECOMMENDATIONS) == CacheTTL.RUN_EVENTS_ACTIVE


def test_is_terminal_run():
    assert is_terminal_run(RunStatus.COMPLETED) is True
    assert is_terminal_run(RunStatus.QUEUED) is False


def test_cache_keys_format():
    assert CacheKeys.user_profile("abc") == "user:abc:profile"
    assert CacheKeys.run_recommendations("run-1") == "run:run-1:recommendations"
    assert CacheKeys.validation_dashboard() == "validation:dashboard"


def test_get_or_load_without_redis():
    service = CacheService()
    service._enabled = False
    service._client = None

    calls = {"count": 0}

    def loader():
        calls["count"] += 1
        return {"value": 1}

    first = service.get_or_load("test:key", 60, loader)
    second = service.get_or_load("test:key", 60, loader)

    assert first == {"value": 1}
    assert second == {"value": 1}
    assert calls["count"] == 2


def test_get_or_load_with_mock_redis():
    service = CacheService()
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    service._client = mock_redis
    service._enabled = True
    service._prefix = "postrec:cache:test"

    result = service.get_or_load("demo", 120, lambda: {"loaded": True})

    assert result == {"loaded": True}
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0] == "postrec:cache:test:demo"
    assert args[1] == 120


def test_invalidate_run_deletes_keys():
    service = CacheService()
    mock_redis = MagicMock()
    service._client = mock_redis
    service._enabled = True
    service._prefix = "postrec:cache:test"

    service.invalidate_run("run-42")

    mock_redis.delete.assert_called_once()
    deleted = mock_redis.delete.call_args[0]
    assert "postrec:cache:test:run:run-42:detail" in deleted
    assert "postrec:cache:test:run:run-42:recommendations" in deleted


def test_delete_pattern_uses_scan_iter():
    service = CacheService()
    mock_redis = MagicMock()
    mock_redis.scan_iter.return_value = [
        "postrec:cache:test:user:1:runs:50",
        "postrec:cache:test:user:1:runs:100",
    ]
    service._client = mock_redis
    service._enabled = True
    service._prefix = "postrec:cache:test"

    service.invalidate_user_runs("1")

    mock_redis.scan_iter.assert_called_once()
    assert mock_redis.delete.call_count == 2
