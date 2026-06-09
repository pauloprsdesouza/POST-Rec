"""In-process TTL cache for OpenAlex taxonomy lookups."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

DEFAULT_TTL_SECONDS = 86_400


@dataclass
class _CacheEntry:
    values: tuple[str, ...]
    expires_at: float


_MEMORY_CACHE: dict[str, _CacheEntry] = {}


def cached_taxonomy_lookup(
    key: str,
    loader: Callable[[], tuple[str, ...]],
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> tuple[str, ...]:
    now = time.time()
    entry = _MEMORY_CACHE.get(key)
    if entry and entry.expires_at > now:
        return entry.values
    values = loader()
    _MEMORY_CACHE[key] = _CacheEntry(values=values, expires_at=now + ttl_seconds)
    return values


def clear_taxonomy_cache() -> None:
    _MEMORY_CACHE.clear()
