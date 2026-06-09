"""Tests for OpenAlex run metrics helpers."""

from packages.postrec_core.retrieval.openalex_metrics import (
    OpenAlexRunMetrics,
    summarize_alignment_stats,
)


def test_openalex_run_metrics_summary():
    metrics = OpenAlexRunMetrics()
    metrics.record_fetch(
        result_count=12,
        cost_usd=0.001,
        latency_ms=120.0,
        use_search=True,
        kind="search",
    )
    metrics.record_fetch(
        result_count=4,
        cost_usd=0.0001,
        latency_ms=80.0,
        use_search=False,
        kind="fallback",
    )
    summary = metrics.summary()
    assert summary["requests"] == 2
    assert summary["search_requests"] == 1
    assert summary["fallback_requests"] == 1
    assert summary["total_hits"] == 16
    assert summary["total_cost_usd"] == 0.0011


def test_summarize_alignment_stats():
    papers = [
        {"domain_alignment_passes": True},
        {"domain_alignment_passes": False, "context_keyword_trap": True},
    ]
    stats = summarize_alignment_stats(papers)
    assert stats["input"] == 2
    assert stats["alignment_passes"] == 1
    assert stats["wrong_field_rate"] == 0.5
    assert stats["keyword_trap_rate"] == 0.5
