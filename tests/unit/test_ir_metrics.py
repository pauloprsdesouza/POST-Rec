"""Tests for IR metrics."""

from packages.postrec_core.evaluation.ir_metrics import (
    dcg_at_k,
    err_at_k,
    hit_at_k,
    map_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_dcg_perfect_order():
    assert dcg_at_k([3, 2, 1], 3) > dcg_at_k([1, 2, 3], 3)


def test_ndcg_perfect():
    assert ndcg_at_k([3, 2, 1], 3) == 1.0


def test_ndcg_empty():
    assert ndcg_at_k([], 5) == 0.0


def test_map_and_mrr():
    relevances = [[1, 0, 1, 0], [0, 0, 1]]
    assert map_at_k(relevances, k=4) > 0
    assert mrr([[0, 1], [1, 0]]) == 0.75


def test_precision_recall_hit():
    rel = [1, 0, 1, 0]
    assert precision_at_k(rel, 2) == 0.5
    assert recall_at_k(rel, 4) == 1.0
    assert hit_at_k(rel, 1) == 1.0


def test_err_at_k():
    # Perfect top result: high ERR
    assert err_at_k([3, 2, 1], 3) > 0.5
    # No relevant docs: ERR should be 0
    assert err_at_k([0, 0, 0], 3) == 0.0
