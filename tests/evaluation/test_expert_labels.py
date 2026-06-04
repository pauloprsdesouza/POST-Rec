"""Expert label correlation helpers."""

from packages.postrec_core.evaluation.expert_labels import correlate_fni_with_expert_originality, spearman_rho


def test_spearman_perfect_monotonic():
    rho = spearman_rho([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
    assert rho is not None
    assert rho > 0.99


def test_correlate_fni_with_expert_originality():
    labels = [
        {"facet_novelty_index": 80, "expert_originality": 6},
        {"facet_novelty_index": 60, "expert_originality": 4},
        {"facet_novelty_index": 40, "expert_originality": 2},
        {"facet_novelty_index": 70, "expert_originality": 5},
    ]
    result = correlate_fni_with_expert_originality(labels)
    assert result["n"] == 4
    assert result["spearman_rho"] is not None
    assert result["spearman_rho"] > 0.8
