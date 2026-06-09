"""Wire Redis taxonomy cache into OpenAlex query builders."""

from __future__ import annotations

from apps.api.features.retrieval.openalex_taxonomy_cache import get_openalex_taxonomy_redis_cache
from packages.postrec_core.retrieval.openalex_query import set_taxonomy_cache_loader

_bootstrapped = False


def ensure_openalex_taxonomy_cache() -> None:
    global _bootstrapped
    if _bootstrapped:
        return
    cache = get_openalex_taxonomy_redis_cache()
    set_taxonomy_cache_loader(cache.get_or_load)
    _bootstrapped = True
