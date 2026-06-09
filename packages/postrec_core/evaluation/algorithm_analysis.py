"""Per-algorithm validation, ranking, observability, and insight metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.postrec_core.evaluation.human_metrics import LIKERT_DIMENSIONS, mean_field, rate
from packages.postrec_core.evaluation.ranking_eval import aggregate_ranking_metrics


def resolve_algorithm(run: dict[str, Any]) -> str:
    return str(run.get("assigned_mode") or run.get("mode") or "unknown")


def build_algorithm_analysis(
    *,
    runs: list[dict[str, Any]],
    feedback_rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    run_metrics: list[dict[str, Any]],
    llm_usage: list[dict[str, Any]],
    surveys: list[dict[str, Any]],
) -> dict[str, Any]:
    run_by_id = {str(r["id"]): r for r in runs}
    algorithms = sorted({resolve_algorithm(run) for run in runs})

    by_algorithm: dict[str, dict[str, Any]] = {}
    for algorithm in algorithms:
        algo_runs = [r for r in runs if resolve_algorithm(r) == algorithm]
        algo_run_ids = {str(r["id"]) for r in algo_runs}
        algo_feedback = [row for row in feedback_rows if str(row.get("run_id")) in algo_run_ids]
        algo_candidates = [c for c in candidates if str(c.get("run_id")) in algo_run_ids]
        algo_run_metrics = [m for m in run_metrics if m.get("algorithm") == algorithm]
        algo_llm = [row for row in llm_usage if str(row.get("run_id")) in algo_run_ids]

        by_algorithm[algorithm] = {
            "algorithm": algorithm,
            "human_rates": _human_rates(algo_feedback),
            "ranking_metrics": aggregate_ranking_metrics(algo_run_metrics),
            "sota_quality": _sota_quality(algo_candidates),
            "observability": _observability(algo_runs, algo_candidates, algo_feedback, algo_llm),
            "insights": _algorithm_insights(algo_feedback, algo_candidates, surveys, algo_run_ids, run_by_id),
        }

    literature_suite = _literature_suite(by_algorithm, run_metrics)
    pairwise = _pairwise_algorithm_tests(by_algorithm)
    engagement_funnel = _engagement_funnel(runs, feedback_rows, surveys, candidates)

    return {
        "algorithms": list(by_algorithm.values()),
        "by_algorithm": by_algorithm,
        "literature_suite": literature_suite,
        "pairwise_tests": pairwise,
        "engagement_funnel": engagement_funnel,
    }


def build_insight_analysis(
    *,
    feedback_rows: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    surveys: list[dict[str, Any]],
    llm_usage: list[dict[str, Any]],
) -> dict[str, Any]:
    run_by_id = {str(r["id"]): r for r in runs}
    candidates_by_run: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        candidates_by_run.setdefault(str(candidate.get("run_id")), []).append(candidate)

    return {
        "decision_distribution": _count_by(feedback_rows, "decision"),
        "would_use_distribution": _count_by(feedback_rows, "would_use_in_real_paper"),
        "dimension_means": {
            dim.replace("_score", ""): mean_field(feedback_rows, dim)
            for dim in LIKERT_DIMENSIONS
            if any(row.get(dim) is not None for row in feedback_rows)
        },
        "cost_vs_quality": _cost_vs_quality(feedback_rows, run_by_id, llm_usage),
        "survey_hit_at_1": _survey_hit_at_1(surveys, candidates_by_run),
        "qualitative_themes": _qualitative_themes(surveys),
    }


def build_observability_summary(
    *,
    runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    feedback_rows: list[dict[str, Any]],
    llm_usage: list[dict[str, Any]],
) -> dict[str, Any]:
    overall = _observability(runs, candidates, feedback_rows, llm_usage)
    by_algorithm: dict[str, Any] = {}
    for algorithm in sorted({resolve_algorithm(r) for r in runs}):
        algo_runs = [r for r in runs if resolve_algorithm(r) == algorithm]
        algo_run_ids = {str(r["id"]) for r in algo_runs}
        by_algorithm[algorithm] = _observability(
            algo_runs,
            [c for c in candidates if str(c.get("run_id")) in algo_run_ids],
            [row for row in feedback_rows if str(row.get("run_id")) in algo_run_ids],
            [row for row in llm_usage if str(row.get("run_id")) in algo_run_ids],
        )
    return {"overall": overall, "by_algorithm": by_algorithm}


def _human_rates(feedback_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not feedback_rows:
        return {
            "feedback_count": 0,
            "average_eas": 0.0,
            "approval_rate": 0.0,
            "would_use_rate": 0.0,
            "save_rate": 0.0,
            "rejection_rate": 0.0,
            "average_relevance": 0.0,
            "average_originality": 0.0,
            "average_clarity": 0.0,
            "average_feasibility": 0.0,
            "average_trust": 0.0,
            "average_usefulness": 0.0,
        }
    return {
        "feedback_count": len(feedback_rows),
        "average_eas": mean_field(feedback_rows, "expectation_alignment_score"),
        "approval_rate": rate(feedback_rows, lambda r: r.get("decision") == "approved"),
        "would_use_rate": rate(feedback_rows, lambda r: r.get("would_use_in_real_paper") == "yes"),
        "maybe_use_rate": rate(feedback_rows, lambda r: r.get("would_use_in_real_paper") == "maybe"),
        "save_rate": rate(feedback_rows, lambda r: r.get("decision") == "save"),
        "rejection_rate": rate(feedback_rows, lambda r: r.get("decision") == "rejected"),
        "average_relevance": mean_field(feedback_rows, "relevance_score"),
        "average_originality": mean_field(feedback_rows, "originality_score"),
        "average_clarity": mean_field(feedback_rows, "clarity_score"),
        "average_feasibility": mean_field(feedback_rows, "feasibility_score"),
        "average_trust": mean_field(feedback_rows, "trust_score"),
        "average_usefulness": mean_field(feedback_rows, "usefulness_score"),
    }


def _sota_quality(candidates: list[dict[str, Any]]) -> dict[str, float]:
    if not candidates:
        return {
            "candidate_count": 0,
            "sota_anchor_rate": 0.0,
            "refinement_rate": 0.0,
            "avg_novelty_verified": 0.0,
            "avg_sota_fit": 0.0,
            "avg_fni": 0.0,
            "avg_gfa": 0.0,
            "avg_fggv_score": 0.0,
        }
    return {
        "candidate_count": len(candidates),
        "sota_anchor_rate": round(
            sum(1 for c in candidates if c.get("has_sota_anchor")) / len(candidates),
            4,
        ),
        "refinement_rate": round(
            sum(1 for c in candidates if c.get("status") == "needs_refinement") / len(candidates),
            4,
        ),
        "avg_novelty_verified": _mean_optional(candidates, "novelty_verified"),
        "avg_sota_fit": _mean_optional(candidates, "sota_fit"),
        "avg_fni": _mean_optional(candidates, "facet_novelty_index"),
        "avg_gfa": _mean_optional(candidates, "gap_alignment_score"),
        "avg_fggv_score": _mean_optional(candidates, "fggv_score"),
    }


def _observability(
    runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    feedback_rows: list[dict[str, Any]],
    llm_usage: list[dict[str, Any]],
) -> dict[str, Any]:
    total_runs = len(runs)
    completed = sum(1 for r in runs if r.get("status") == "completed")
    failed = sum(1 for r in runs if r.get("status") in {"failed", "failed_schema_validation"})
    durations = [_run_duration_seconds(r) for r in runs]
    durations = [value for value in durations if value is not None]

    run_costs = [float(r.get("estimated_cost_usd") or 0) for r in runs]
    llm_costs = [float(row.get("estimated_cost_usd") or 0) for row in llm_usage]
    llm_tokens = [int(row.get("total_tokens") or 0) for row in llm_usage]

    candidate_count = len(candidates)
    feedback_count = len(feedback_rows)

    return {
        "run_count": total_runs,
        "completed_runs": completed,
        "failed_runs": failed,
        "completion_rate": round(completed / total_runs, 4) if total_runs else 0.0,
        "failure_rate": round(failed / total_runs, 4) if total_runs else 0.0,
        "avg_duration_seconds": round(sum(durations) / len(durations), 2) if durations else None,
        "median_duration_seconds": _median(durations),
        "total_cost_usd": round(sum(run_costs) + sum(llm_costs), 4),
        "avg_cost_per_run_usd": round((sum(run_costs) + sum(llm_costs)) / total_runs, 4) if total_runs else 0.0,
        "avg_tokens_per_run": round(sum(llm_tokens) / total_runs, 2) if total_runs else 0.0,
        "candidates_generated": candidate_count,
        "feedback_submitted": feedback_count,
        "feedback_coverage_rate": round(feedback_count / candidate_count, 4) if candidate_count else 0.0,
        "avg_candidates_per_run": round(candidate_count / total_runs, 2) if total_runs else 0.0,
        "avg_feedback_per_run": round(feedback_count / total_runs, 2) if total_runs else 0.0,
    }


def _algorithm_insights(
    feedback_rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    surveys: list[dict[str, Any]],
    run_ids: set[str],
    run_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    algo_surveys = [s for s in surveys if s.get("run_id") and str(s.get("run_id")) in run_ids]
    return {
        "decision_mix": _count_by(feedback_rows, "decision"),
        "would_use_mix": _count_by(feedback_rows, "would_use_in_real_paper"),
        "survey_count": len(algo_surveys),
        "expectation_met_mean": mean_field(algo_surveys, "expectation_met_score") if algo_surveys else 0.0,
    }


def _literature_suite(
    by_algorithm: dict[str, dict[str, Any]],
    run_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    """Standard IR / recommender metrics cited in top evaluation papers."""
    overall = aggregate_ranking_metrics(run_metrics)
    references = [
        {
            "metric": "NDCG@K",
            "citation": "Järvelin & Kekäläinen (2002); standard in RecSys/TREC",
            "use": "Ranking quality with graded user relevance",
        },
        {
            "metric": "MAP",
            "citation": "Manning et al. (2008); IR evaluation textbook standard",
            "use": "Precision across recall levels for binary relevance",
        },
        {
            "metric": "MRR",
            "citation": "Voorhees (1999); QA and recommendation benchmarks",
            "use": "Rank of first relevant item",
        },
        {
            "metric": "ERR@K",
            "citation": "Chapelle et al. (2009, WSDM)",
            "use": "Expected Reciprocal Rank with graded satisfaction",
        },
        {
            "metric": "Precision@K / Recall@K",
            "citation": "Herlocker et al. (2004); recommender systems handbook",
            "use": "Top-K hit rate vs full relevant set",
        },
        {
            "metric": "Hit@K / Success@K",
            "citation": "Common in Spotify/MovieLens-style offline eval",
            "use": "Session success when any top-K item is relevant",
        },
        {
            "metric": "Spearman ρ / Kendall τ",
            "citation": "Rank correlation; Si et al. (2025) ideation eval",
            "use": "System rank vs user preference order",
        },
        {
            "metric": "FDS (facet diversity)",
            "citation": "POST-Rec FGGV paper; Scideator diversity line",
            "use": "List diversity without duplicate facets",
        },
    ]
    return {
        "overall": overall,
        "by_algorithm": {algo: data["ranking_metrics"] for algo, data in by_algorithm.items()},
        "references": references,
    }


def _pairwise_algorithm_tests(by_algorithm: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        by_algorithm.values(),
        key=lambda item: item["human_rates"]["feedback_count"],
        reverse=True,
    )
    if len(ranked) < 2:
        return []

    results = []
    for index in range(len(ranked) - 1):
        left = ranked[index]
        right = ranked[index + 1]
        if left["human_rates"]["feedback_count"] < 3 or right["human_rates"]["feedback_count"] < 3:
            continue
        # Placeholder: real EAS lists would need per-row retention; use summary comparison note
        results.append(
            {
                "algorithm_a": left["algorithm"],
                "algorithm_b": right["algorithm"],
                "eas_delta": round(
                    left["human_rates"]["average_eas"] - right["human_rates"]["average_eas"],
                    4,
                ),
                "ndcg5_delta": round(
                    left["ranking_metrics"].get("ndcg@5", 0) - right["ranking_metrics"].get("ndcg@5", 0),
                    4,
                ),
                "approval_delta": round(
                    left["human_rates"]["approval_rate"] - right["human_rates"]["approval_rate"],
                    4,
                ),
            }
        )
    return results


def _engagement_funnel(
    runs: list[dict[str, Any]],
    feedback_rows: list[dict[str, Any]],
    surveys: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, str | int | float]]:
    return [
        {"stage": "runs", "count": len(runs)},
        {"stage": "completed_runs", "count": sum(1 for r in runs if r.get("status") == "completed")},
        {"stage": "candidates", "count": len(candidates)},
        {"stage": "feedback", "count": len(feedback_rows)},
        {"stage": "surveys", "count": len(surveys)},
    ]


def _cost_vs_quality(
    feedback_rows: list[dict[str, Any]],
    run_by_id: dict[str, dict[str, Any]],
    llm_usage: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cost_by_run: dict[str, float] = {}
    for row in llm_usage:
        run_id = str(row.get("run_id"))
        cost_by_run[run_id] = cost_by_run.get(run_id, 0.0) + float(row.get("estimated_cost_usd") or 0)

    buckets: dict[str, list[float]] = {}
    for row in feedback_rows:
        run = run_by_id.get(str(row.get("run_id")), {})
        algorithm = resolve_algorithm(run)
        eas = row.get("expectation_alignment_score")
        if eas is None:
            continue
        buckets.setdefault(algorithm, []).append(float(eas))

    points = []
    for algorithm, eas_values in sorted(buckets.items()):
        algo_runs = [r for r in run_by_id.values() if resolve_algorithm(r) == algorithm]
        total_cost = sum(
            float(r.get("estimated_cost_usd") or 0) + cost_by_run.get(str(r.get("id")), 0.0) for r in algo_runs
        )
        points.append(
            {
                "algorithm": algorithm,
                "average_eas": round(sum(eas_values) / len(eas_values), 4),
                "avg_cost_per_run_usd": round(total_cost / len(algo_runs), 4) if algo_runs else 0.0,
                "feedback_count": len(eas_values),
            }
        )
    return points


def _survey_hit_at_1(
    surveys: list[dict[str, Any]],
    candidates_by_run: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    hits = 0
    total = 0
    for survey in surveys:
        run_id = survey.get("run_id")
        most_useful = survey.get("most_useful_recommendation_id")
        if not run_id or not most_useful:
            continue
        run_candidates = candidates_by_run.get(str(run_id), [])
        if not run_candidates:
            continue
        top = max(run_candidates, key=lambda c: float(c.get("final_score") or 0))
        total += 1
        if str(top.get("id")) == str(most_useful):
            hits += 1
    return {
        "count": total,
        "hit_at_1": round(hits / total, 4) if total else None,
    }


def _qualitative_themes(surveys: list[dict[str, Any]]) -> dict[str, int]:
    themes = {"what_helped_most": 0, "what_hurt_most": 0, "free_comment": 0}
    for survey in surveys:
        if survey.get("what_helped_most"):
            themes["what_helped_most"] += 1
        if survey.get("what_hurt_most"):
            themes["what_hurt_most"] += 1
        if survey.get("free_comment"):
            themes["free_comment"] += 1
    return themes


def _count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _run_duration_seconds(run: dict[str, Any]) -> float | None:
    started = run.get("started_at") or run.get("created_at")
    finished = run.get("finished_at")
    if not started or not finished:
        return None
    try:
        start_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(str(finished).replace("Z", "+00:00"))
        return max(0.0, (end_dt - start_dt).total_seconds())
    except ValueError:
        return None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 2)
    return round((ordered[mid - 1] + ordered[mid]) / 2, 2)


def _mean_optional(rows: list[dict[str, Any]], field: str) -> float:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
