"""Tests for article-topic validation before idea generation."""

from unittest.mock import MagicMock, patch

from apps.api.features.recommendations.article_validation import article_validation_service
from apps.api.features.recommendations.llm import GeminiService, assign_paper_ids
from packages.postrec_core.prompts.article_validation import ARTICLE_VALIDATION_USER_TEMPLATE
from packages.postrec_core.prompts.recommendation_prompt import RECOMMENDATION_USER_TEMPLATE


def test_assign_paper_ids_adds_stable_labels():
    papers = [{"title": "Paper A"}, {"title": "Paper B", "paper_id": "PX"}]
    result = assign_paper_ids(papers)
    assert result[0]["paper_id"] == "P1"
    assert result[1]["paper_id"] == "PX"


def test_recommendation_prompt_formats_with_paper_context():
    rendered = RECOMMENDATION_USER_TEMPLATE.format(
        research_area="Recommender Systems",
        seed_topics="GNN, collaborative filtering",
        expected_output="Research ideas",
        desired_depth="medium",
        constraints="{}",
        user_expectations="none",
        papers_context="[P1] Example paper (2024) tier=sota_recent relevance=0.9",
        max_recommendations=3,
    )
    assert "PHASE 1" in rendered
    assert "paper_id" in rendered
    assert "Recommender Systems" in rendered


def test_article_validation_prompt_includes_rubric():
    rendered = ARTICLE_VALIDATION_USER_TEMPLATE.format(
        research_area="ML",
        seed_topics="topic A",
        avoided_topics="none",
        papers_context="[P1] Title",
        min_score=0.5,
        min_valid_papers=3,
    )
    assert "Relevance rubric" in rendered
    assert "Self-verification" in rendered


def test_deterministic_filter_removes_irrelevant_papers():
    papers = [
        {
            "paper_id": "P1",
            "title": "Graph neural networks for recommender systems",
            "abstract": "GNN collaborative filtering study.",
        },
        {
            "paper_id": "P2",
            "title": "Medieval crop rotation",
            "abstract": "Historical agriculture.",
        },
    ]
    filtered, stats, _scored_all = article_validation_service._deterministic_filter(
        papers,
        research_area="Recommender Systems",
        seed_topics=["recommender systems"],
        avoided_topics=None,
        min_score=0.22,
        min_valid=1,
    )
    assert stats["kept"] == 1
    assert filtered[0]["paper_id"] == "P1"
    assert filtered[0]["llm_passes_validation"] is True


@patch("apps.api.features.recommendations.article_validation.persist_article_validation_scores")
@patch("apps.api.features.recommendations.article_validation.get_settings")
@patch("apps.api.features.recommendations.article_validation.gemini_service")
def test_llm_validation_merges_scores(mock_gemini, mock_settings, mock_persist):
    mock_settings.return_value = MagicMock(
        article_llm_validation_enabled=True,
        gemini_api_key="key",
        article_llm_min_relevance_score=0.5,
        article_min_valid_papers=1,
        article_sparse_corpus_threshold=12,
        article_grounding_best_effort_enabled=False,
        retrieval_min_relevance_score=0.22,
        retrieval_min_domain_alignment=0.40,
        retrieval_domain_filter_enabled=True,
        retrieval_openalex_fwci_boost_enabled=False,
    )
    papers = [
        {"paper_id": "P1", "title": "Recommender GNN", "abstract": "graphs for recsys"},
        {"paper_id": "P2", "title": "Unrelated history", "abstract": "medieval"},
    ]
    mock_gemini.validate_retrieved_papers.return_value = {
        "papers": [
            {**papers[0], "llm_relevance_score": 0.9, "llm_passes_validation": True},
            {**papers[1], "llm_relevance_score": 0.1, "llm_passes_validation": False},
        ],
        "validations": [],
        "sufficient_evidence": True,
    }

    filtered, stats = article_validation_service.validate_and_filter(
        MagicMock(),
        "run-1",
        papers,
        research_area="Recommender Systems",
        seed_topics=["recommender systems"],
    )
    assert stats["method"] == "llm"
    assert len(filtered) == 1
    assert filtered[0]["paper_id"] == "P1"
    mock_persist.assert_called_once()


@patch("apps.api.features.recommendations.article_validation.persist_article_validation_scores")
@patch("apps.api.features.recommendations.article_validation.get_settings")
@patch("apps.api.features.recommendations.article_validation.gemini_service")
def test_llm_validation_uses_paper_count_not_llm_flag(mock_gemini, mock_settings, mock_persist):
    mock_settings.return_value = MagicMock(
        article_llm_validation_enabled=True,
        gemini_api_key="key",
        article_llm_min_relevance_score=0.42,
        article_min_valid_papers=2,
        article_sparse_corpus_threshold=12,
        article_grounding_best_effort_enabled=False,
        retrieval_min_relevance_score=0.22,
        retrieval_min_domain_alignment=0.40,
        retrieval_domain_filter_enabled=True,
        retrieval_openalex_fwci_boost_enabled=False,
    )
    papers = [
        {"paper_id": "P1", "title": "Recsys GNN", "abstract": "graphs"},
        {"paper_id": "P2", "title": "Social capital in networks", "abstract": "network analysis"},
        {"paper_id": "P3", "title": "User engagement", "abstract": "engagement metrics"},
    ]
    mock_gemini.validate_retrieved_papers.return_value = {
        "papers": [
            {**papers[0], "llm_relevance_score": 0.8, "llm_passes_validation": True},
            {**papers[1], "llm_relevance_score": 0.7, "llm_passes_validation": True},
            {**papers[2], "llm_relevance_score": 0.6, "llm_passes_validation": True},
        ],
        "validations": [],
        "sufficient_evidence": False,
        "insufficient_evidence_reason": (
            "Only 3 papers passed validation, which is less than the required minimum of 3."
        ),
    }

    filtered, stats = article_validation_service.validate_and_filter(
        MagicMock(),
        "run-1",
        papers,
        research_area="Recommender Systems",
        seed_topics=["social capital"],
    )

    assert stats["method"] == "llm"
    assert stats["sufficient_evidence"] is True
    assert len(filtered) == 3


@patch("apps.api.features.recommendations.article_validation.persist_article_validation_scores")
@patch("apps.api.features.recommendations.article_validation.get_settings")
@patch("apps.api.features.recommendations.article_validation.gemini_service")
def test_best_effort_proceeds_when_strict_validation_fails(mock_gemini, mock_settings, mock_persist):
    mock_settings.return_value = MagicMock(
        article_llm_validation_enabled=True,
        gemini_api_key="key",
        article_llm_min_relevance_score=0.42,
        article_min_valid_papers=2,
        article_sparse_corpus_threshold=12,
        article_grounding_best_effort_enabled=True,
        retrieval_min_relevance_score=0.22,
        retrieval_min_domain_alignment=0.40,
        retrieval_domain_filter_enabled=True,
        retrieval_openalex_fwci_boost_enabled=False,
    )
    papers = [
        {"paper_id": "P1", "title": "Quantum chromodynamics in colliders", "abstract": "particle physics"},
        {"paper_id": "P2", "title": "Medieval European crop rotation", "abstract": "historical agriculture"},
    ]
    mock_gemini.validate_retrieved_papers.return_value = {
        "papers": [
            {**papers[0], "llm_relevance_score": 0.35, "llm_passes_validation": False},
            {**papers[1], "llm_relevance_score": 0.3, "llm_passes_validation": False},
        ],
        "validations": [],
        "sufficient_evidence": False,
    }

    filtered, stats = article_validation_service.validate_and_filter(
        MagicMock(),
        "run-1",
        papers,
        research_area="Recommender Systems",
        seed_topics=["social capital"],
    )

    assert stats["sufficient_evidence"] is True
    assert stats["best_effort_grounding"] is True
    assert len(filtered) >= 1


def test_merge_paper_validations_applies_llm_scores():
    papers = [{"paper_id": "P1", "title": "A"}, {"paper_id": "P2", "title": "B"}]
    result = GeminiService._merge_paper_validations(
        papers,
        {
            "validations": [
                {
                    "paper_id": "P1",
                    "relevance_score": 0.88,
                    "passes_validation": True,
                    "matched_topics": ["recsys"],
                    "match_rationale": "title match",
                    "avoided_topic_hit": False,
                }
            ],
            "sufficient_evidence": True,
        },
    )
    by_id = {paper["paper_id"]: paper for paper in result["papers"]}
    assert by_id["P1"]["llm_relevance_score"] == 0.88
    assert by_id["P1"]["llm_passes_validation"] is True
