"""Offline evaluation harness for baseline vs FGGV comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.evaluation.baselines import (
    ABLATION_METHODS,
    BASELINE_DESCRIPTIONS,
    CORE_METHODS,
    BaselineMethod,
)
from packages.postrec_core.evaluation.metrics import discriminability
from packages.postrec_core.facets.facet_map import build_literature_facet_map
from packages.postrec_core.facets.gap_facet_alignment import compute_gap_facet_alignment
from packages.postrec_core.scoring.facet_diversity import average_pairwise_facet_diversity, select_facet_diverse
from packages.postrec_core.scoring.facet_grounded_ranking import (
    FggvAblation,
    compute_facet_novelty_index,
    compute_fggv_score,
    count_false_novel_facets,
)
from packages.postrec_core.scoring.novelty_verification import (
    claim_overlap_novelty,
    compute_sota_fit,
    proposal_text,
)
from packages.postrec_core.scoring.verified_ranking import compute_verified_final_score
from packages.postrec_core.validation.recommendation_validator import validate_recommendation

DEFAULT_FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_eval_topics.json"


def _document_novelty(proposal: dict[str, Any], papers: list[dict[str, Any]]) -> float:
    corpus = [f"{p.get('title', '')}. {p.get('abstract', '')}" for p in papers]
    return claim_overlap_novelty(proposal_text(proposal), corpus)


def _fggv_ablation_for(method: BaselineMethod) -> FggvAblation:
    if method == BaselineMethod.M_FGGV_NO_GFA:
        return FggvAblation.NO_GFA
    if method == BaselineMethod.M_FGGV_NO_CFN:
        return FggvAblation.NO_CFN
    return FggvAblation.FULL


def _score_fggv(
    proposal: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    verified: float,
    doc_novelty: float,
    gap_matrix: dict[str, Any] | None,
    method: BaselineMethod,
) -> dict[str, Any]:
    facet_map = build_literature_facet_map(papers)
    use_saturation = method != BaselineMethod.M_FGGV_NO_SATURATION
    fni, per_facet, diagnostics = compute_facet_novelty_index(
        proposal,
        facet_map,
        use_saturation_weights=use_saturation,
    )
    gas = compute_gap_facet_alignment(proposal, gap_matrix)
    ablation = _fggv_ablation_for(method)
    fggv = compute_fggv_score(
        verified_final_score=verified,
        facet_novelty_index=fni,
        gap_alignment_score=gas,
        document_novelty_verified=doc_novelty,
        ablation=ablation,
    )
    false_novel_facets = count_false_novel_facets(per_facet)
    return {
        "facet_novelty_index": round(fni * 100, 2),
        "gap_alignment_score": round(gas * 100, 2),
        "fggv_score": fggv,
        "per_facet_novelty": {k: round(v * 100, 2) for k, v in per_facet.items()},
        "false_novel_facet_count": false_novel_facets,
        "low_novelty_facets": diagnostics.get("low_novelty_facets"),
        "primary_ranking_score": fggv,
    }


def _score_proposal(
    proposal: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    method: BaselineMethod,
    gap_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scores = dict(proposal.get("scores") or {})
    doc_novelty = _document_novelty(proposal, papers)
    sota_fit = compute_sota_fit(proposal, papers)
    mode = RunMode.FGGV if method.value.startswith("m_fggv") else (
        RunMode.SOTA if method != BaselineMethod.B1_QUICK else RunMode.QUICK
    )

    validation = validate_recommendation(proposal, papers, mode=mode)
    verified = compute_verified_final_score(
        scores,
        sota_fit=sota_fit,
        novelty_verified=doc_novelty,
        mode=mode,
    )

    result: dict[str, Any] = {
        "method": method.value,
        "document_novelty": round(doc_novelty * 100, 2),
        "verified_final_score": verified,
        "sota_fit": round(sota_fit * 100, 2),
        "validation_status": validation.publication_status,
        "validation_issues": validation.issues,
    }

    if method.value.startswith("m_fggv"):
        result.update(
            _score_fggv(
                proposal,
                papers,
                verified=verified,
                doc_novelty=doc_novelty,
                gap_matrix=gap_matrix,
                method=method,
            )
        )
    elif method == BaselineMethod.B3_RAG_NO_VERIFY:
        result["primary_ranking_score"] = float(scores.get("final_score") or scores.get("novelty") or 0)
    else:
        result["primary_ranking_score"] = verified

    return result


def _diversity_comparison(topic: dict[str, Any]) -> dict[str, float]:
    """Compare list diversity with vs without FDS on good+weak pool."""
    proposals = [topic["good_proposal"], topic["weak_proposal"]]
    naive = proposals[:1]
    diverse = select_facet_diverse(proposals, max_items=1, lambda_param=0.7)
    return {
        "naive_pairwise_diversity": average_pairwise_facet_diversity(naive),
        "fds_pairwise_diversity": average_pairwise_facet_diversity(diverse),
        "pool_pairwise_diversity": average_pairwise_facet_diversity(proposals),
    }


def run_offline_evaluation(
    fixture_path: Path | None = None,
    *,
    include_ablations: bool = False,
) -> dict[str, Any]:
    """Score good vs weak proposals across baselines for paper-ready tables."""
    path = fixture_path or DEFAULT_FIXTURE
    payload = json.loads(path.read_text(encoding="utf-8"))
    topics = payload.get("topics") or []

    methods: tuple[BaselineMethod, ...] = CORE_METHODS
    if include_ablations:
        methods = CORE_METHODS + ABLATION_METHODS

    per_topic: list[dict[str, Any]] = []
    summary: dict[str, dict[str, Any]] = {}
    diversity_by_topic: list[dict[str, Any]] = []

    for method in methods:
        good_scores: list[float] = []
        weak_scores: list[float] = []
        false_novel_good: list[int] = []
        false_novel_weak: list[int] = []
        for topic in topics:
            papers = topic.get("papers") or []
            gap_matrix = topic.get("gap_matrix")
            good = _score_proposal(topic["good_proposal"], papers, method=method, gap_matrix=gap_matrix)
            weak = _score_proposal(topic["weak_proposal"], papers, method=method, gap_matrix=gap_matrix)
            good_scores.append(float(good["primary_ranking_score"]))
            weak_scores.append(float(weak["primary_ranking_score"]))
            if method == BaselineMethod.M_FGGV:
                false_novel_good.append(int(good.get("false_novel_facet_count") or 0))
                false_novel_weak.append(int(weak.get("false_novel_facet_count") or 0))
                diversity_by_topic.append(
                    {"topic_id": topic.get("id"), **_diversity_comparison(topic)},
                )
            per_topic.append(
                {
                    "topic_id": topic.get("id"),
                    "method": method.value,
                    "good": good,
                    "weak": weak,
                }
            )
        disc = discriminability(good_scores, weak_scores)
        entry: dict[str, Any] = {
            "description": BASELINE_DESCRIPTIONS[method],
            "good_mean": disc.good_mean,
            "weak_mean": disc.weak_mean,
            "delta": disc.delta,
            "separation_ratio": disc.separation_ratio,
        }
        if method == BaselineMethod.M_FGGV and false_novel_good:
            entry["false_novel_facet_count_good_mean"] = round(
                sum(false_novel_good) / len(false_novel_good), 2
            )
            entry["false_novel_facet_count_weak_mean"] = round(
                sum(false_novel_weak) / len(false_novel_weak), 2
            )
        summary[method.value] = entry

    return {
        "fixture": str(path),
        "topic_count": len(topics),
        "baseline_descriptions": {m.value: BASELINE_DESCRIPTIONS[m] for m in methods},
        "summary": summary,
        "per_topic": per_topic,
        "diversity_fds": diversity_by_topic,
        "sota_positioning": _positioning_assessment(summary),
    }


def _positioning_assessment(summary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Heuristic artifact-level assessment (not a substitute for human study)."""
    fggv = summary.get(BaselineMethod.M_FGGV.value, {})
    b2 = summary.get(BaselineMethod.B2_SOTA_PIPELINE.value, {})
    fggv_delta = float(fggv.get("delta") or 0)
    b2_delta = float(b2.get("delta") or 0)
    offline_beats_b2 = fggv_delta > b2_delta
    return {
        "offline_discriminability_beats_b2": offline_beats_b2,
        "fggv_delta": fggv_delta,
        "b2_delta": b2_delta,
        "claim_ahead_of_sota_requires_human_study": True,
        "implemented_differentiators": [
            "joint_gap_matrix_and_facet_deltas",
            "saturation_aware_fni",
            "per_facet_false_novel_guard",
            "llm_facet_critic",
            "facet_diversity_selection",
        ],
    }
