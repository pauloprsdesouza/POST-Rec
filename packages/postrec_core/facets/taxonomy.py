"""Facet taxonomy for literature-grounded novelty verification."""

from enum import StrEnum


class FacetType(StrEnum):
    """Research idea facets aligned with Scideator / Idea Novelty Checker literature."""

    PROBLEM = "problem"
    METHOD = "method"
    DATA = "data"
    EVALUATION = "evaluation"

    @classmethod
    def all_ordered(cls) -> tuple["FacetType", ...]:
        return (cls.PROBLEM, cls.METHOD, cls.DATA, cls.EVALUATION)


FACET_WEIGHTS: dict[FacetType, float] = {
    FacetType.PROBLEM: 0.30,
    FacetType.METHOD: 0.35,
    FacetType.DATA: 0.15,
    FacetType.EVALUATION: 0.20,
}
