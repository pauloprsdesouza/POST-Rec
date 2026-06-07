"""Saturation-aware facet weighting for underserved-gap targeting."""

from __future__ import annotations

from packages.postrec_core.facets.taxonomy import FACET_WEIGHTS, FacetType


def underserved_facets(saturation: dict[str, float], *, threshold: float = 0.45) -> list[str]:
    """Facet types mentioned in fewer than threshold fraction of papers."""
    return [facet.value for facet in FacetType.all_ordered() if saturation.get(facet.value, 1.0) < threshold]


def saturation_adjusted_weights(saturation: dict[str, float], *, boost: float = 0.5) -> dict[str, float]:
    """Re-weight FNI toward under-served facets (novel vs Scideator-style uniform facets)."""
    raw: dict[str, float] = {}
    for facet in FacetType.all_ordered():
        sat = max(0.0, min(1.0, float(saturation.get(facet.value, 0.5))))
        raw[facet.value] = FACET_WEIGHTS[facet] * (1.0 + boost * (1.0 - sat))
    total = sum(raw.values()) or 1.0
    return {key: value / total for key, value in raw.items()}


def saturation_novelty_multiplier(
    facet: FacetType | str,
    saturation: dict[str, float],
    *,
    penalty_strength: float = 0.35,
) -> float:
    """Penalize near-duplicate ideas in saturated facets; neutral for sparse facets."""
    key = facet.value if isinstance(facet, FacetType) else str(facet)
    sat = max(0.0, min(1.0, float(saturation.get(key, 0.5))))
    return max(0.55, 1.0 - penalty_strength * sat)
