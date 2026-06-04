"""Unit tests for verified ranking."""

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.scoring.verified_ranking import compute_verified_final_score


def test_compute_verified_final_score_includes_sota_signals():
    scores = {
        "relevance": 80,
        "novelty": 70,
        "evidence": 75,
        "feasibility": 85,
        "trend": 60,
        "publication_potential": 65,
        "strategic_fit": 70,
    }
    final = compute_verified_final_score(
        scores,
        sota_fit=0.9,
        novelty_verified=0.85,
        mode=RunMode.SOTA,
    )
    assert 70 <= final <= 100


def test_sota_mode_weights_recent_signals_higher():
    scores = {
        "relevance": 70,
        "novelty": 70,
        "evidence": 70,
        "feasibility": 70,
        "trend": 70,
        "publication_potential": 70,
        "strategic_fit": 70,
    }
    low_sota = compute_verified_final_score(
        scores,
        sota_fit=0.2,
        novelty_verified=0.2,
        mode=RunMode.SOTA,
    )
    high_sota = compute_verified_final_score(
        scores,
        sota_fit=0.95,
        novelty_verified=0.95,
        mode=RunMode.SOTA,
    )
    assert high_sota > low_sota
