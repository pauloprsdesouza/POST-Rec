"""Tests for research project roadmap service."""

from apps.api.features.projects.service import _fallback_roadmap
from apps.api.shared.models import RecommendationCandidate


def test_fallback_roadmap_has_six_phases_with_tasks():
    recommendation = RecommendationCandidate(
        title="Facet-aware gap verification for ideation",
        research_gap="No joint facet-level verification in ideation systems",
        research_question="How does facet grounding affect novelty?",
        hypothesis="FGGV improves perceived novelty",
        proposed_method="Build facet maps and verify gaps",
        experimental_plan="Run ablation on curated topics",
        datasets=["OpenAlex corpus"],
        evaluation_metrics=["NDCG@5", "approval rate"],
        risks=["LLM bias"],
        evidence_papers=[{"paper_id": "P1", "title": "Prior work", "year": 2024}],
    )

    roadmap = _fallback_roadmap(recommendation)

    assert len(roadmap["phases"]) == 6
    for phase in roadmap["phases"]:
        assert len(phase["tasks"]) >= 4
        assert phase["tasks"][0]["title"]
