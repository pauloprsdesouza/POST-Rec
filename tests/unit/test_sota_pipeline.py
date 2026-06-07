"""Tests for SOTA pipeline orchestration."""

from unittest.mock import MagicMock, patch

from apps.api.features.recommendations.pipeline import sota_pipeline_service
from packages.postrec_core.domain.run_mode import RunMode


@patch("apps.api.features.recommendations.pipeline.gemini_service")
@patch("apps.api.features.recommendations.pipeline.novelty_verification_service")
def test_quick_mode_calls_enhanced_generation(mock_verify, mock_gemini):
    mock_gemini.generate_recommendations.return_value = {
        "recommendations": [{"title": "Idea", "scores": {"novelty": 70}}]
    }
    mock_verify.verify_recommendation.side_effect = (
        lambda db, run_id, rec, papers, embeddings, *, mode, sota_landscape=None, **kwargs: rec
    )
    mock_verify.filter_publishable.side_effect = lambda recs, **kwargs: recs

    db = MagicMock()
    papers = [{"title": "Paper", "year": 2025, "tier": "sota_recent"}]
    result = sota_pipeline_service.generate(
        db=db,
        run_id="00000000-0000-4000-8000-000000000001",
        mode=RunMode.QUICK,
        research_area="AI",
        seed_topics=["graphs"],
        expected_output="ideas",
        desired_depth="medium",
        constraints={},
        papers=papers,
        paper_embeddings=[[0.1, 0.2]],
        max_recommendations=3,
    )

    mock_gemini.generate_recommendations.assert_called_once()
    assert mock_gemini.generate_recommendations.call_args.kwargs["enhanced_sota_fields"] is True
    assert len(result) == 1
