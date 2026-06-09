"""Tests for research report builder."""

from packages.postrec_core.evaluation.report_builder import build_research_report


def test_build_research_report_empty():
    report = build_research_report(
        {
            "sessions": [],
            "runs": [],
            "feedback": [],
            "surveys": [],
            "candidates": [],
            "expert_labels": [],
        }
    )
    assert report["schema_version"] == "1.1"
    assert report["sample"]["feedback"] == 0
    assert report["primary_outcomes"]["average_eas"] == 0.0


def test_build_research_report_with_feedback():
    report = build_research_report(
        {
            "sessions": [{"id": "s1"}],
            "runs": [
                {
                    "id": "r1",
                    "mode": "sota",
                    "status": "completed",
                    "created_at": "2026-01-15T10:00:00+00:00",
                }
            ],
            "feedback": [
                {
                    "run_id": "r1",
                    "recommendation_id": "c1",
                    "relevance_score": 4,
                    "originality_score": 5,
                    "clarity_score": 4,
                    "feasibility_score": 3,
                    "trust_score": 4,
                    "usefulness_score": 5,
                    "decision": "approved",
                    "would_use_in_real_paper": "yes",
                    "expectation_alignment_score": 4.2,
                    "created_at": "2026-01-15T11:00:00+00:00",
                },
                {
                    "run_id": "r1",
                    "recommendation_id": "c2",
                    "relevance_score": 2,
                    "originality_score": 2,
                    "clarity_score": 3,
                    "feasibility_score": 3,
                    "trust_score": 2,
                    "usefulness_score": 2,
                    "decision": "rejected",
                    "would_use_in_real_paper": "no",
                    "expectation_alignment_score": 2.1,
                    "created_at": "2026-01-15T11:05:00+00:00",
                },
            ],
            "surveys": [
                {
                    "expectation_met_score": 4,
                    "would_use_again": True,
                    "would_recommend": True,
                    "created_at": "2026-01-15T12:00:00+00:00",
                }
            ],
            "candidates": [
                {
                    "id": "c1",
                    "run_id": "r1",
                    "status": "published",
                    "final_score": 90,
                    "has_sota_anchor": True,
                    "novelty_verified": 80,
                    "sota_fit": 75,
                },
                {
                    "id": "c2",
                    "run_id": "r1",
                    "status": "published",
                    "final_score": 40,
                    "has_sota_anchor": False,
                    "novelty_verified": 30,
                    "sota_fit": 35,
                },
            ],
            "expert_labels": [],
        }
    )
    assert report["sample"]["feedback"] == 2
    assert report["primary_outcomes"]["approval_rate"] == 0.5
    assert report["ranking_metrics"]["overall"]["run_count"] == 1
    assert len(report["descriptive_statistics"]) == 6
    assert "algorithm_analysis" in report
    assert report["algorithm_analysis"]["algorithms"][0]["algorithm"] == "sota"
    assert "observability" in report
    assert "insight_analysis" in report
