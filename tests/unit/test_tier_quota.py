"""Unit tests for tier quota selection."""

from packages.postrec_core.retrieval.tier_quota import apply_tier_quotas


def test_apply_tier_quotas_respects_max_papers():
    papers = [{"title": f"P{i}", "tier": "sota_recent" if i < 4 else "seminal"} for i in range(10)]
    selected = apply_tier_quotas(papers, 5, sota_quota=0.6)
    assert len(selected) == 5


def test_apply_tier_quotas_prioritizes_recent_sota():
    papers = [
        {"title": "Recent 1", "tier": "sota_recent"},
        {"title": "Recent 2", "tier": "sota_recent"},
        {"title": "Seminal", "tier": "seminal"},
        {"title": "Other", "tier": "peripheral"},
    ]
    selected = apply_tier_quotas(papers, 3, sota_quota=0.67)
    recent_count = sum(1 for p in selected if p["tier"] == "sota_recent")
    assert recent_count >= 2
