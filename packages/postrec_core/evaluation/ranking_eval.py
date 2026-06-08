"""Per-run ranking evaluation using user feedback as graded relevance."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.evaluation.correlation import rank_correlation
from packages.postrec_core.evaluation.ir_metrics import (
    err_at_k,
    hit_at_k,
    map_at_k,
    mean_metric,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    success_at_k,
)


def graded_relevance(feedback: dict[str, Any]) -> float:
    """Map user feedback to [0, 1] graded relevance."""
    usefulness = feedback.get("usefulness_score")
    originality = feedback.get("originality_score")
    if usefulness is not None and originality is not None:
        return round((float(usefulness) + float(originality)) / 10.0, 4)
    if usefulness is not None:
        return round(float(usefulness) / 5.0, 4)
    if feedback.get("decision") == "approved":
        return 1.0
    if feedback.get("decision") == "rejected":
        return 0.0
    return 0.2


def binary_relevance(feedback: dict[str, Any], threshold: float = 0.5) -> float:
    return 1.0 if graded_relevance(feedback) >= threshold else 0.0


def evaluate_run_ranking(
    candidates: list[dict[str, Any]],
    feedback_by_candidate: dict[str, dict[str, Any]],
    *,
    k_values: tuple[int, ...] = (1, 3, 5, 10),
) -> dict[str, Any] | None:
    """Evaluate system ranking vs user preferences for one run."""
    rated = [candidate for candidate in candidates if str(candidate.get("id")) in feedback_by_candidate]
    if len(rated) < 2:
        return None

    system_sorted = sorted(
        rated,
        key=lambda c: float(c.get("final_score") or 0),
        reverse=True,
    )
    user_sorted = sorted(
        rated,
        key=lambda c: graded_relevance(feedback_by_candidate[str(c.get("id"))]),
        reverse=True,
    )

    system_relevances = [graded_relevance(feedback_by_candidate[str(c.get("id"))]) for c in system_sorted]
    binary_relevances = [binary_relevance(feedback_by_candidate[str(c.get("id"))]) for c in system_sorted]

    system_ranks = [float(c.get("final_score") or 0) for c in system_sorted]
    user_ranks = [graded_relevance(feedback_by_candidate[str(c.get("id"))]) for c in user_sorted]

    ndcg = {f"ndcg@{k}": ndcg_at_k(system_relevances, k) for k in k_values}
    pr = {f"precision@{k}": precision_at_k(binary_relevances, k) for k in k_values}
    rc = {f"recall@{k}": recall_at_k(binary_relevances, k) for k in k_values}
    hits = {f"hit@{k}": hit_at_k(binary_relevances, k) for k in k_values}
    succ = {f"success@{k}": success_at_k(binary_relevances, k) for k in k_values}
    err = {f"err@{k}": err_at_k(system_relevances, k) for k in k_values if k in (3, 5, 10)}

    return {
        "rated_count": len(rated),
        **ndcg,
        **err,
        "map": map_at_k([binary_relevances], k=None),
        "mrr": mrr([binary_relevances]),
        **pr,
        **rc,
        **hits,
        **succ,
        "rank_correlation": rank_correlation(system_ranks, user_ranks),
    }


def aggregate_ranking_metrics(run_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not run_metrics:
        return {
            "run_count": 0,
            "ndcg@1": 0.0,
            "ndcg@3": 0.0,
            "ndcg@5": 0.0,
            "ndcg@10": 0.0,
            "err@3": 0.0,
            "err@5": 0.0,
            "err@10": 0.0,
            "map": 0.0,
            "mrr": 0.0,
            "precision@1": 0.0,
            "precision@3": 0.0,
            "precision@5": 0.0,
            "precision@10": 0.0,
            "recall@1": 0.0,
            "recall@3": 0.0,
            "recall@5": 0.0,
            "recall@10": 0.0,
            "hit@1": 0.0,
            "hit@3": 0.0,
            "hit@5": 0.0,
            "hit@10": 0.0,
            "success@1": 0.0,
            "success@5": 0.0,
            "success@10": 0.0,
            "mean_spearman_rho": None,
            "mean_kendall_tau": None,
        }

    keys = [
        "ndcg@1",
        "ndcg@3",
        "ndcg@5",
        "ndcg@10",
        "err@3",
        "err@5",
        "err@10",
        "map",
        "mrr",
        "precision@1",
        "precision@3",
        "precision@5",
        "precision@10",
        "recall@1",
        "recall@3",
        "recall@5",
        "recall@10",
        "hit@1",
        "hit@3",
        "hit@5",
        "hit@10",
        "success@1",
        "success@5",
        "success@10",
    ]
    aggregated = {key: mean_metric([m[key] for m in run_metrics if key in m]) for key in keys}
    rhos = [
        m["rank_correlation"]["spearman_rho"]
        for m in run_metrics
        if m.get("rank_correlation", {}).get("spearman_rho") is not None
    ]
    taus = [
        m["rank_correlation"]["kendall_tau"]
        for m in run_metrics
        if m.get("rank_correlation", {}).get("kendall_tau") is not None
    ]
    aggregated["run_count"] = len(run_metrics)
    aggregated["mean_spearman_rho"] = mean_metric(rhos) if rhos else None
    aggregated["mean_kendall_tau"] = mean_metric(taus) if taus else None
    return aggregated
