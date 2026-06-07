"""Reusable cache-aside helpers for API read paths."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from apps.api.shared.infra.cache import cache_service

T = TypeVar("T")


def load_cached_json(
    key: str,
    ttl: int,
    loader: Callable[[], T],
    *,
    terminal: bool,
) -> T:
    """Load JSON-backed data with terminal vs active run caching behavior."""
    if terminal:
        return cache_service.get_or_load(key, ttl, loader)

    cached = cache_service.get_json(key)
    if cached is not None:
        return cached

    value = loader()
    if value is not None:
        cache_service.set_json(key, value, ttl)
    return value
