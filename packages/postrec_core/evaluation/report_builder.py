"""Build comprehensive research report from analysis datasets."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from packages.postrec_core.evaluation.algorithm_analysis import (
    build_algorithm_analysis,
    build_insight_analysis,
    build_observability_summary,
    resolve_algorithm,
)
from packages.postrec_core.evaluation.expert_labels import correlate_fni_with_expert_originality
from packages.postrec_core.evaluation.human_metrics import (
    all_dimension_statistics,
    cronbach_alpha,
    mean_field,
    rate,
)
from packages.postrec_core.evaluation.inferential import _test_to_dict, chi_square_2x2, compare_groups
from packages.postrec_core.evaluation.ranking_eval import aggregate_ranking_metrics, evaluate_run_ranking


def build_research_report(data: dict[str, Any]) -> dict[str, Any]:
    """Assemble full statistical report for reviewers/co-authors."""
    feedback_rows = data.get("feedback") or []
    runs = data.get("runs") or []
    candidates = data.get("candidates") or []
    surveys = data.get("surveys") or []
    sessions = data.get("sessions") or []
    expert_labels = data.get("expert_labels") or []
    llm_usage = data.get("llm_usage") or []

    candidates_by_run: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        run_id = str(candidate.get("run_id"))
        candidates_by_run.setdefault(run_id, []).append(candidate)

    feedback_by_run: dict[str, list[dict[str, Any]]] = {}
    feedback_by_candidate: dict[str, dict[str, Any]] = {}
    for row in feedback_rows:
        run_id = str(row.get("run_id"))
        feedback_by_run.setdefault(run_id, []).append(row)
        feedback_by_candidate[str(row.get("recommendation_id"))] = row

    run_metrics = []
    for run in runs:
        run_id = str(run.get("id"))
        if run_id not in candidates_by_run:
            continue
        metrics = evaluate_run_ranking(
            candidates_by_run[run_id],
            feedback_by_candidate,
        )
        if metrics:
            algorithm = resolve_algorithm(run)
            run_metrics.append(
                {
                    **metrics,
                    "run_id": run_id,
                    "mode": run.get("mode"),
                    "algorithm": algorithm,
                }
            )

    ranking_overall = aggregate_ranking_metrics(run_metrics)
    ranking_by_algorithm: dict[str, Any] = {}
    for algorithm in sorted({m.get("algorithm") for m in run_metrics if m.get("algorithm")}):
        algo_metrics = [m for m in run_metrics if m.get("algorithm") == algorithm]
        ranking_by_algorithm[algorithm] = aggregate_ranking_metrics(algo_metrics)

    algorithm_analysis = build_algorithm_analysis(
        runs=runs,
        feedback_rows=feedback_rows,
        candidates=candidates,
        run_metrics=run_metrics,
        llm_usage=llm_usage,
        surveys=surveys,
    )
    observability = build_observability_summary(
        runs=runs,
        candidates=candidates,
        feedback_rows=feedback_rows,
        llm_usage=llm_usage,
    )
    insight_analysis = build_insight_analysis(
        feedback_rows=feedback_rows,
        runs=runs,
        candidates=candidates,
        surveys=surveys,
        llm_usage=llm_usage,
    )

    descriptive = all_dimension_statistics(feedback_rows)
    alpha = cronbach_alpha(feedback_rows)

    primary_outcomes = {
        "average_eas": mean_field(feedback_rows, "expectation_alignment_score"),
        "approval_rate": rate(feedback_rows, lambda r: r.get("decision") == "approved"),
        "would_use_rate": rate(feedback_rows, lambda r: r.get("would_use_in_real_paper") == "yes"),
        "average_originality": mean_field(feedback_rows, "originality_score"),
        "average_usefulness": mean_field(feedback_rows, "usefulness_score"),
        "average_trust": mean_field(feedback_rows, "trust_score"),
        "average_feasibility": mean_field(feedback_rows, "feasibility_score"),
        "cronbach_alpha": alpha,
    }

    survey_outcomes = {
        "count": len(surveys),
        "expectation_met_mean": mean_field(surveys, "expectation_met_score"),
        "would_use_again_rate": rate(surveys, lambda s: bool(s.get("would_use_again"))),
        "would_recommend_rate": rate(surveys, lambda s: bool(s.get("would_recommend"))),
    }

    sota_outcomes = {
        "candidate_count": len(candidates),
        "sota_anchor_rate": _sota_anchor_rate(candidates),
        "refinement_rate": _refinement_rate(candidates),
        "avg_novelty_verified": _mean_score_field(candidates, "novelty_verified"),
        "avg_sota_fit": _mean_score_field(candidates, "sota_fit"),
        "avg_fni": _mean_score_field(candidates, "facet_novelty_index"),
        "avg_gfa": _mean_score_field(candidates, "gap_alignment_score"),
    }

    experiment = _experiment_analysis(feedback_rows, runs)
    correlations = _score_correlations(feedback_rows, candidates)
    rejection_summary = _rejection_summary(feedback_rows)
    weekly_trends = _weekly_trends(feedback_rows, runs, surveys)
    expert_analysis = correlate_fni_with_expert_originality(expert_labels) if expert_labels else None

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "schema_version": "1.1",
        "sample": {
            "sessions": len(sessions),
            "runs": len(runs),
            "completed_runs": sum(1 for r in runs if r.get("status") == "completed"),
            "feedback": len(feedback_rows),
            "surveys": len(surveys),
            "candidates": len(candidates),
            "rated_runs": len(run_metrics),
            "algorithms": len(algorithm_analysis.get("algorithms") or []),
        },
        "primary_outcomes": primary_outcomes,
        "descriptive_statistics": descriptive,
        "survey_outcomes": survey_outcomes,
        "sota_quality": sota_outcomes,
        "ranking_metrics": {
            "overall": ranking_overall,
            "by_algorithm": ranking_by_algorithm,
            "by_mode": ranking_by_algorithm,
            "per_run": run_metrics,
        },
        "algorithm_analysis": algorithm_analysis,
        "observability": observability,
        "insight_analysis": insight_analysis,
        "experiment_analysis": experiment,
        "mode_comparison": [
            {
                "mode": item["algorithm"],
                "algorithm": item["algorithm"],
                **item["human_rates"],
            }
            for item in algorithm_analysis["algorithms"]
        ],
        "score_correlations": correlations,
        "rejection_summary": rejection_summary,
        "weekly_trends": weekly_trends,
        "expert_label_analysis": expert_analysis,
        "methodology_notes": {
            "relevance_mapping": "Graded relevance = (usefulness + originality) / 10",
            "binary_threshold": 0.5,
            "primary_test": "Mann-Whitney U for Likert; Chi-square for approval rates",
            "ranking_k_values": [1, 3, 5, 10],
            "algorithm_key": "assigned_mode when present, else run mode (quick/sota/fggv/exploratory)",
            "literature_metrics": (
                "NDCG, MAP, MRR, ERR, P@K, R@K, Hit@K per Järvelin (2002), Chapelle (2009), Herlocker (2004)"
            ),
        },
    }


def _sota_anchor_rate(candidates: list[dict[str, Any]]) -> float:
    if not candidates:
        return 0.0
    with_anchor = sum(1 for c in candidates if c.get("has_sota_anchor"))
    return round(with_anchor / len(candidates), 4)


def _refinement_rate(candidates: list[dict[str, Any]]) -> float:
    if not candidates:
        return 0.0
    refined = sum(1 for c in candidates if c.get("status") == "needs_refinement")
    return round(refined / len(candidates), 4)


def _mean_score_field(candidates: list[dict[str, Any]], field: str) -> float:
    values = [float(c[field]) for c in candidates if c.get(field) is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _experiment_analysis(feedback_rows: list[dict], runs: list[dict]) -> dict[str, Any] | None:
    run_by_id = {str(r["id"]): r for r in runs}
    experiment_rows = [
        row for row in feedback_rows if run_by_id.get(str(row.get("run_id")), {}).get("experiment_variant")
    ]
    if not experiment_rows:
        return None

    variants: dict[str, list[dict]] = {}
    for row in experiment_rows:
        run = run_by_id.get(str(row.get("run_id")), {})
        variant = run.get("experiment_variant") or "unknown"
        variants.setdefault(variant, []).append(row)

    if len(variants) < 2:
        return {"variants": _variant_summaries(variants), "hypothesis_tests": None}

    control = variants.get("control", [])
    treatment = variants.get("treatment", [])
    tests = {
        "eas": compare_groups(
            [
                float(r["expectation_alignment_score"])
                for r in control
                if r.get("expectation_alignment_score") is not None
            ],
            [
                float(r["expectation_alignment_score"])
                for r in treatment
                if r.get("expectation_alignment_score") is not None
            ],
            label_a="control (SOTA)",
            label_b="treatment (FGGV)",
        ),
        "originality": compare_groups(
            [float(r["originality_score"]) for r in control if r.get("originality_score") is not None],
            [float(r["originality_score"]) for r in treatment if r.get("originality_score") is not None],
            label_a="control (SOTA)",
            label_b="treatment (FGGV)",
        ),
        "approval_rate": _test_to_dict(
            chi_square_2x2(
                sum(1 for r in control if r.get("decision") == "approved"),
                len(control),
                sum(1 for r in treatment if r.get("decision") == "approved"),
                len(treatment),
            )
        ),
        "would_use_rate": _test_to_dict(
            chi_square_2x2(
                sum(1 for r in control if r.get("would_use_in_real_paper") == "yes"),
                len(control),
                sum(1 for r in treatment if r.get("would_use_in_real_paper") == "yes"),
                len(treatment),
            )
        ),
    }
    return {"variants": _variant_summaries(variants), "hypothesis_tests": tests}


def _variant_summaries(variants: dict[str, list[dict]]) -> list[dict[str, Any]]:
    summaries = []
    for variant, rows in sorted(variants.items()):
        summaries.append(
            {
                "variant": variant,
                "feedback_count": len(rows),
                "average_eas": mean_field(rows, "expectation_alignment_score"),
                "average_originality": mean_field(rows, "originality_score"),
                "approval_rate": rate(rows, lambda r: r.get("decision") == "approved"),
                "would_use_rate": rate(rows, lambda r: r.get("would_use_in_real_paper") == "yes"),
            }
        )
    return summaries


def _score_correlations(feedback_rows: list[dict], candidates: list[dict]) -> list[dict[str, Any]]:
    from packages.postrec_core.evaluation.correlation import pearson_r, spearman_rho

    candidate_by_id = {str(c["id"]): c for c in candidates}
    pairs: dict[str, tuple[list[float], list[float]]] = {}

    system_fields = [
        ("final_score", "usefulness_score"),
        ("novelty_verified", "originality_score"),
        ("facet_novelty_index", "originality_score"),
        ("sota_fit", "trust_score"),
        ("fggv_score", "originality_score"),
    ]

    for row in feedback_rows:
        candidate = candidate_by_id.get(str(row.get("recommendation_id")))
        if not candidate:
            continue
        for system_field, user_field in system_fields:
            sys_val = candidate.get(system_field)
            user_val = row.get(user_field)
            if sys_val is None or user_val is None:
                continue
            pairs.setdefault(f"{system_field}_vs_{user_field}", ([], []))
            pairs[f"{system_field}_vs_{user_field}"][0].append(float(sys_val))
            pairs[f"{system_field}_vs_{user_field}"][1].append(float(user_val))

    results = []
    for name, (x, y) in sorted(pairs.items()):
        if len(x) < 3:
            continue
        results.append(
            {
                "pair": name,
                "n": len(x),
                "spearman_rho": spearman_rho(x, y),
                "pearson_r": pearson_r(x, y),
            }
        )
    return results


def _rejection_summary(feedback_rows: list[dict]) -> dict[str, Any]:
    rejected = [r for r in feedback_rows if r.get("decision") == "rejected"]
    comments = [r["comment"] for r in rejected if r.get("comment")]
    return {
        "rejection_count": len(rejected),
        "rejection_rate": rate(feedback_rows, lambda r: r.get("decision") == "rejected"),
        "comments": comments[:50],
        "comment_count": len(comments),
    }


def _weekly_trends(
    feedback_rows: list[dict],
    runs: list[dict],
    surveys: list[dict],
) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}

    def week_key(iso_date: str | None) -> str | None:
        if not iso_date:
            return None
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            year, week, _ = dt.isocalendar()
            return f"{year}-W{week:02d}"
        except ValueError:
            return None

    for row in feedback_rows:
        key = week_key(row.get("created_at"))
        if not key:
            continue
        bucket = buckets.setdefault(key, {"week": key, "feedback_count": 0, "eas_values": [], "runs": 0, "surveys": 0})
        bucket["feedback_count"] += 1
        if row.get("expectation_alignment_score") is not None:
            bucket["eas_values"].append(float(row["expectation_alignment_score"]))

    for run in runs:
        key = week_key(run.get("created_at"))
        if key and key in buckets:
            buckets[key]["runs"] += 1

    for survey in surveys:
        key = week_key(survey.get("created_at"))
        if key and key in buckets:
            buckets[key]["surveys"] += 1

    trends = []
    for key in sorted(buckets):
        bucket = buckets[key]
        eas_values = bucket.pop("eas_values")
        bucket["average_eas"] = round(sum(eas_values) / len(eas_values), 4) if eas_values else None
        trends.append(bucket)
    return trends
