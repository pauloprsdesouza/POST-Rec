"""Tests for in-process OpenAlex taxonomy cache."""

from packages.postrec_core.retrieval.openalex_taxonomy_cache import (
    cached_taxonomy_lookup,
    clear_taxonomy_cache,
)


def test_cached_taxonomy_lookup_deduplicates_loader_calls():
    clear_taxonomy_cache()
    calls = {"count": 0}

    def loader() -> tuple[str, ...]:
        calls["count"] += 1
        return ("T1", "T2")

    first = cached_taxonomy_lookup("topics:test", loader, ttl_seconds=60)
    second = cached_taxonomy_lookup("topics:test", loader, ttl_seconds=60)
    assert first == ("T1", "T2")
    assert second == first
    assert calls["count"] == 1
