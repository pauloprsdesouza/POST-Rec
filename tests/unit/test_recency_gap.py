"""Tests for recency gap scoring."""

from packages.postrec_core.scoring.recency_gap import compute_recency_gap


def test_compute_recency_gap_with_recent_anchors():
    recommendation = {
        "proposed_method": "efficient subgraph training pipeline",
        "sota_anchors": [{"title": "Recent Paper", "year": 2025}],
    }
    papers = [{"title": "Recent Paper", "year": 2025, "tier": "sota_recent"}]
    gap = compute_recency_gap(recommendation, papers)
    assert 0.0 <= gap <= 1.0
