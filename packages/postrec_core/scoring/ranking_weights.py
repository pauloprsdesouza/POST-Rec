"""Mode-specific ranking weight profiles."""

from dataclasses import dataclass

from packages.postrec_core.domain.run_mode import RunMode


@dataclass(frozen=True)
class RankingWeights:
    relevance: float
    novelty: float
    evidence: float
    feasibility: float
    trend: float
    publication_potential: float
    strategic_fit: float
    sota_fit: float
    novelty_verified: float

    def as_dimension_dict(self) -> dict[str, float]:
        return {
            "relevance": self.relevance,
            "novelty": self.novelty,
            "evidence": self.evidence,
            "feasibility": self.feasibility,
            "trend": self.trend,
            "publication_potential": self.publication_potential,
            "strategic_fit": self.strategic_fit,
        }


DEFAULT_WEIGHTS = RankingWeights(
    relevance=0.18,
    novelty=0.12,
    evidence=0.13,
    feasibility=0.12,
    trend=0.08,
    publication_potential=0.08,
    strategic_fit=0.08,
    sota_fit=0.11,
    novelty_verified=0.10,
)

SOTA_WEIGHTS = RankingWeights(
    relevance=0.16,
    novelty=0.10,
    evidence=0.12,
    feasibility=0.11,
    trend=0.07,
    publication_potential=0.07,
    strategic_fit=0.07,
    sota_fit=0.16,
    novelty_verified=0.14,
)

EXPLORATORY_WEIGHTS = RankingWeights(
    relevance=0.14,
    novelty=0.16,
    evidence=0.10,
    feasibility=0.10,
    trend=0.08,
    publication_potential=0.08,
    strategic_fit=0.08,
    sota_fit=0.10,
    novelty_verified=0.16,
)

FGGV_WEIGHTS = RankingWeights(
    relevance=0.14,
    novelty=0.08,
    evidence=0.11,
    feasibility=0.10,
    trend=0.06,
    publication_potential=0.06,
    strategic_fit=0.06,
    sota_fit=0.14,
    novelty_verified=0.10,
)


def weights_for_mode(mode: RunMode) -> RankingWeights:
    if mode == RunMode.FGGV:
        return FGGV_WEIGHTS
    if mode == RunMode.EXPLORATORY:
        return EXPLORATORY_WEIGHTS
    if mode == RunMode.SOTA:
        return SOTA_WEIGHTS
    return DEFAULT_WEIGHTS
