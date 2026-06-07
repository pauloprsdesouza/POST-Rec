"""Expectation Alignment Score calculation."""

from typing import Any


def would_use_to_score(value: str | None) -> float:
    mapping = {"yes": 5.0, "maybe": 3.0, "no": 1.0}
    return mapping.get(value or "", 3.0)


def compute_eas(feedback: dict[str, Any]) -> float:
    """Compute Expectation Alignment Score per SDD formula."""
    usefulness = float(feedback.get("usefulness_score", 3))
    relevance = float(feedback.get("relevance_score", 3))
    clarity = float(feedback.get("clarity_score", 3))
    feasibility = float(feedback.get("feasibility_score", 3))
    trust = float(feedback.get("trust_score", 3))
    would_use = would_use_to_score(feedback.get("would_use_in_real_paper"))

    return 0.25 * usefulness + 0.20 * relevance + 0.20 * clarity + 0.15 * feasibility + 0.10 * trust + 0.10 * would_use


def compute_final_ranking_score(scores: dict[str, float]) -> float:
    """Compute final ranking score per SDD formula."""
    return (
        0.22 * scores.get("relevance", 0)
        + 0.18 * scores.get("novelty", 0)
        + 0.15 * scores.get("evidence", 0)
        + 0.15 * scores.get("feasibility", 0)
        + 0.10 * scores.get("trend", 0)
        + 0.10 * scores.get("publication_potential", 0)
        + 0.10 * scores.get("strategic_fit", 0)
    )
