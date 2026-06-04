"""Tests for dual-pass merge."""

from packages.postrec_core.retrieval.dual_pass import merge_dual_pass_results


def test_merge_dual_pass_respects_sota_quota():
    sota = [{"title": f"Recent {i}", "year": 2025, "citation_count": 1} for i in range(4)]
    foundation = [{"title": f"Classic {i}", "year": 2010, "citation_count": 200} for i in range(4)]
    merged = merge_dual_pass_results(sota, foundation, max_papers=5, sota_quota=0.6)
    assert len(merged) == 5
    recent = sum(1 for p in merged if p.get("retrieval_pass") == "sota")
    assert recent >= 3
