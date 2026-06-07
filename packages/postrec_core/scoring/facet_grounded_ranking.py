"""Contrastive Facet Novelty (CFN) and Facet-Grounded ranking."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from packages.postrec_core.facets.extraction import extract_proposal_facets
from packages.postrec_core.facets.facet_map import LiteratureFacetMap
from packages.postrec_core.facets.saturation import (
    saturation_adjusted_weights,
    saturation_novelty_multiplier,
)
from packages.postrec_core.facets.taxonomy import FACET_WEIGHTS, FacetType
from packages.postrec_core.retrieval.hybrid_ranking import cosine_similarity
from packages.postrec_core.scoring.novelty_verification import claim_overlap_novelty, token_set

DEFAULT_MIN_PER_FACET_NOVELTY = 0.28


class FggvAblation(StrEnum):
    FULL = "full"
    NO_GFA = "no_gfa"
    NO_CFN = "no_cfn"
    NO_SATURATION = "no_saturation"


def contrastive_facet_novelty_token(
    proposal_facet: str,
    corpus_facets: list[str],
) -> float:
    """Token-level facet novelty (testable without embeddings)."""
    if not proposal_facet.strip():
        return 0.0
    return claim_overlap_novelty(proposal_facet, corpus_facets or [""])


def contrastive_facet_novelty_embedding(
    proposal_embedding: list[float],
    corpus_embeddings: list[list[float]],
) -> float:
    if not proposal_embedding or not corpus_embeddings:
        return 0.5
    max_sim = max(cosine_similarity(proposal_embedding, emb) for emb in corpus_embeddings)
    return max(0.0, min(1.0, 1.0 - max_sim))


def _closest_corpus_match(
    proposal_text: str,
    corpus_meta: list[dict[str, str]],
    *,
    facet_embeddings: list[float] | None = None,
    corpus_embeddings: list[list[float]] | None = None,
) -> dict[str, Any]:
    if not proposal_text.strip():
        return {"paper_title": None, "similarity": 0.0, "excerpt": ""}

    if facet_embeddings and corpus_embeddings and corpus_embeddings:
        sims = [cosine_similarity(facet_embeddings, emb) for emb in corpus_embeddings]
        best_idx = max(range(len(sims)), key=lambda i: sims[i])
        meta = corpus_meta[best_idx] if best_idx < len(corpus_meta) else {}
        return {
            "paper_title": meta.get("paper_title"),
            "similarity": round(sims[best_idx], 4),
            "excerpt": (meta.get("text") or "")[:120],
        }

    best_sim = 0.0
    best_meta: dict[str, str] = {}
    prop_tokens = token_set(proposal_text)
    for meta in corpus_meta:
        text = meta.get("text") or ""
        other = token_set(text)
        if not prop_tokens or not other:
            continue
        sim = len(prop_tokens & other) / len(prop_tokens | other)
        if sim > best_sim:
            best_sim = sim
            best_meta = meta
    return {
        "paper_title": best_meta.get("paper_title"),
        "similarity": round(best_sim, 4),
        "excerpt": (best_meta.get("text") or "")[:120],
    }


def compute_facet_novelty_index(
    recommendation: dict[str, Any],
    facet_map: LiteratureFacetMap,
    *,
    facet_embeddings: dict[str, list[float]] | None = None,
    corpus_facet_embeddings: dict[str, list[list[float]]] | None = None,
    llm_per_facet_scores: dict[str, float] | None = None,
    llm_blend: float = 0.25,
    use_saturation_weights: bool = True,
) -> tuple[float, dict[str, float], dict[str, Any]]:
    """Facet Novelty Index (FNI) with optional saturation-aware weighting and LLM blend."""
    proposal_facets = extract_proposal_facets(recommendation)
    per_facet: dict[str, float] = {}
    closest_matches: dict[str, Any] = {}
    weights = (
        saturation_adjusted_weights(facet_map.saturation)
        if use_saturation_weights
        else {facet.value: FACET_WEIGHTS[facet] for facet in FacetType.all_ordered()}
    )

    for facet in FacetType.all_ordered():
        text = proposal_facets.get(facet.value, "").strip()
        corpus_texts = facet_map.corpus_texts_for(facet)
        corpus_meta = facet_map.corpus_meta_for(facet)
        prop_emb = (facet_embeddings or {}).get(facet.value)
        corp_embs = (corpus_facet_embeddings or {}).get(facet.value, [])

        if prop_emb and corp_embs:
            raw = contrastive_facet_novelty_embedding(prop_emb, corp_embs)
        else:
            raw = contrastive_facet_novelty_token(text, corpus_texts)

        if use_saturation_weights:
            raw = max(0.0, min(1.0, raw * saturation_novelty_multiplier(facet, facet_map.saturation)))

        llm_score = None
        if llm_per_facet_scores and facet.value in llm_per_facet_scores:
            llm_score = max(0.0, min(1.0, llm_per_facet_scores[facet.value] / 100.0))
            raw = max(0.0, min(1.0, (1.0 - llm_blend) * raw + llm_blend * llm_score))

        per_facet[facet.value] = raw
        closest_matches[facet.value] = _closest_corpus_match(
            text,
            corpus_meta,
            facet_embeddings=prop_emb,
            corpus_embeddings=corp_embs or None,
        )

    weighted = sum(weights.get(facet.value, 0.0) * per_facet.get(facet.value, 0.0) for facet in FacetType.all_ordered())
    diagnostics = {
        "closest_facet_matches": closest_matches,
        "facet_weights": {k: round(v, 4) for k, v in weights.items()},
        "low_novelty_facets": [
            facet.value
            for facet in FacetType.all_ordered()
            if per_facet.get(facet.value, 0.0) < DEFAULT_MIN_PER_FACET_NOVELTY
        ],
    }
    return max(0.0, min(1.0, weighted)), per_facet, diagnostics


def count_false_novel_facets(per_facet: dict[str, float], *, min_novelty: float = DEFAULT_MIN_PER_FACET_NOVELTY) -> int:
    return sum(1 for value in per_facet.values() if value < min_novelty)


def compute_fggv_score(
    *,
    verified_final_score: float,
    facet_novelty_index: float,
    gap_alignment_score: float,
    document_novelty_verified: float,
    ablation: FggvAblation = FggvAblation.FULL,
) -> float:
    """FGGV composite score (0–100) for ranking and paper evaluation."""
    fni = max(0.0, min(1.0, facet_novelty_index))
    gas = max(0.0, min(1.0, gap_alignment_score))
    doc = max(0.0, min(1.0, document_novelty_verified))
    base = max(0.0, min(100.0, verified_final_score)) / 100.0

    if ablation == FggvAblation.NO_CFN:
        fni = doc
    if ablation == FggvAblation.NO_GFA:
        gas = 0.5

    composite = 0.30 * base + 0.32 * fni + 0.23 * gas + 0.15 * doc
    return round(max(0.0, min(100.0, composite * 100.0)), 2)


def facet_diversity_key(recommendation: dict[str, Any]) -> str:
    """Stable key for diversity selection from facet text."""
    facets = extract_proposal_facets(recommendation)
    return " | ".join(facets.get(f.value, "") for f in FacetType.all_ordered())


def facet_token_diversity(recommendation: dict[str, Any]) -> set[str]:
    return token_set(facet_diversity_key(recommendation))
