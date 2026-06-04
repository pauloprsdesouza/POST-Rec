"""Tests for saturation-aware FGGV helpers."""

from packages.postrec_core.facets.saturation import saturation_adjusted_weights, underserved_facets


def test_underserved_facets_detects_sparse_types():
    saturation = {"problem": 0.9, "method": 0.8, "data": 0.2, "evaluation": 0.3}
    under = underserved_facets(saturation, threshold=0.45)
    assert "data" in under
    assert "evaluation" in under
    assert "problem" not in under


def test_saturation_adjusted_weights_sum_to_one():
    weights = saturation_adjusted_weights({"problem": 0.9, "method": 0.2, "data": 0.5, "evaluation": 0.5})
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    assert weights["method"] > weights["problem"]
