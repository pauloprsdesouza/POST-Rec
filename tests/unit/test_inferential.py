"""Tests for inferential statistics."""

from packages.postrec_core.evaluation.inferential import (
    chi_square_2x2,
    cliffs_delta,
    cohens_d,
    compare_groups,
    mann_whitney_u,
    welch_t_test,
)


def test_cohens_d_positive():
    d = cohens_d([5, 6, 7, 8], [1, 2, 3, 4])
    assert d is not None
    assert d > 0


def test_cliffs_delta():
    delta = cliffs_delta([5, 6, 7], [1, 2, 3])
    assert delta is not None
    assert delta > 0


def test_mann_whitney_detects_difference():
    result = mann_whitney_u([5, 6, 7, 8, 9], [1, 2, 3, 4, 5])
    assert result.group_a_n == 5
    assert result.p_value is not None
    assert result.p_value < 0.05


def test_welch_t_test():
    result = welch_t_test([5, 6, 7, 8], [1, 2, 3, 4])
    assert result.significant_at_005


def test_chi_square():
    result = chi_square_2x2(8, 10, 2, 10)
    assert result.significant_at_005


def test_compare_groups_structure():
    result = compare_groups([4, 5, 6], [2, 3, 4], label_a="A", label_b="B")
    assert result["label_a"] == "A"
    assert "mann_whitney" in result
    assert "welch_t_test" in result
