"""Unit tests for Expectation Alignment Score."""

from packages.postrec_core.scoring.expectation_alignment import (
    compute_eas,
    compute_final_ranking_score,
)


def test_compute_eas_perfect_scores():
    feedback = {
        "usefulness_score": 5,
        "relevance_score": 5,
        "clarity_score": 5,
        "feasibility_score": 5,
        "trust_score": 5,
        "would_use_in_real_paper": "yes",
    }
    eas = compute_eas(feedback)
    assert eas == 5.0


def test_compute_eas_would_use_maybe():
    feedback = {
        "usefulness_score": 3,
        "relevance_score": 3,
        "clarity_score": 3,
        "feasibility_score": 3,
        "trust_score": 3,
        "would_use_in_real_paper": "maybe",
    }
    eas = compute_eas(feedback)
    assert 2.5 < eas < 3.5


def test_compute_final_ranking_score():
    scores = {
        "relevance": 0.8,
        "novelty": 0.7,
        "evidence": 0.6,
        "feasibility": 0.9,
        "trend": 0.5,
        "publication_potential": 0.7,
        "strategic_fit": 0.8,
    }
    result = compute_final_ranking_score(scores)
    assert 0.0 < result < 1.0
