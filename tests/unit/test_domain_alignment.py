"""Tests for research-context alignment across academic fields."""

from unittest.mock import patch

from apps.api.features.retrieval.relevance import compute_relevance_score, filter_and_rank_papers
from packages.postrec_core.retrieval.context_alignment import (
    build_research_context,
    compute_context_alignment,
    infer_expected_fields,
)


def test_infer_expected_fields_from_research_area():
    assert "computer_science" in infer_expected_fields("Recommender Systems")
    assert "psychology" in infer_expected_fields("Clinical Psychology")
    assert "medicine_health" in infer_expected_fields("Clinical Medicine")


def test_recsys_social_capital_cs_paper_passes():
    paper = {
        "title": "Social capital-aware graph neural networks for recommender systems",
        "abstract": "We integrate social network signals into profile modeling and collaborative filtering.",
        "venue": "RecSys",
        "source": "openalex",
    }
    alignment = compute_context_alignment(
        paper,
        research_area="Recommender Systems",
        topics=["social capital", "social networks", "profile modeling"],
    )
    assert alignment.passes is True
    assert alignment.score >= 0.55
    assert "computer_science" in alignment.expected_fields


def test_sociology_social_capital_paper_rejected_for_recsys():
    paper = {
        "title": "Social capital in rural communities",
        "abstract": "A qualitative sociological study of community networks and agriculture.",
        "venue": "American Journal of Sociology",
    }
    topics = ["social capital", "social networks", "profile modeling"]
    alignment = compute_context_alignment(
        paper,
        research_area="Recommender Systems",
        topics=topics,
    )
    assert alignment.passes is False
    assert alignment.keyword_trap is True

    with patch(
        "apps.api.features.retrieval.relevance.qualis_service.apply_relevance_boost", side_effect=lambda s, p: (s, {})
    ):
        score = compute_relevance_score(
            paper,
            topics=topics,
            research_area="Recommender Systems",
        )
    assert score < 0.22


def test_psychology_paper_rejected_even_with_profile_modeling_terms():
    paper = {
        "title": "Personality profile modeling and social network support in adolescents",
        "abstract": "We conducted a clinical psychology survey on mental health and peer networks.",
        "venue": "Journal of Personality and Social Psychology",
    }
    alignment = compute_context_alignment(
        paper,
        research_area="Recommender Systems",
        topics=["social capital", "social networks", "profile modeling"],
    )
    assert alignment.passes is False


def test_psychology_area_accepts_psychology_paper_rejects_cs_paper():
    psych_paper = {
        "title": "Depression and social network support in adolescents",
        "abstract": "A psychometric survey on mental health and personality in psychology participants.",
        "venue": "Journal of Personality and Social Psychology",
    }
    cs_paper = {
        "title": "Graph neural networks for collaborative filtering",
        "abstract": "We benchmark neural recommenders on public datasets.",
        "venue": "RecSys",
    }
    topics = ["adolescent depression", "social networks"]

    psych_alignment = compute_context_alignment(
        psych_paper,
        research_area="Clinical Psychology",
        topics=topics,
    )
    cs_alignment = compute_context_alignment(
        cs_paper,
        research_area="Clinical Psychology",
        topics=topics,
    )
    assert psych_alignment.passes is True
    assert cs_alignment.passes is False


def test_medicine_area_accepts_clinical_ml_bridge():
    paper = {
        "title": "Deep learning for diabetic retinopathy diagnosis",
        "abstract": "We evaluate a neural network on a clinical cohort of patients in hospital screening.",
        "venue": "The Lancet Digital Health",
    }
    alignment = compute_context_alignment(
        paper,
        research_area="Clinical Medicine",
        topics=["diabetes", "machine learning"],
    )
    assert alignment.passes is True


def test_medicine_area_rejects_unrelated_agriculture_keyword_match():
    paper = {
        "title": "Crop rotation effects on soil diabetes indicators",
        "abstract": "An agricultural field study without clinical patients or hospital data.",
        "venue": "Journal of Agronomy",
    }
    alignment = compute_context_alignment(
        paper,
        research_area="Clinical Medicine",
        topics=["diabetes", "machine learning"],
    )
    assert alignment.passes is False


def test_filter_and_rank_drops_off_domain_sociology_paper():
    papers = [
        {
            "title": "Social capital-aware recommender systems with profile modeling",
            "abstract": "Graph neural collaborative filtering on social networks.",
            "venue": "ACM RecSys",
            "citation_count": 40,
        },
        {
            "title": "Social capital among nursing home residents",
            "abstract": "Clinical gerontology study of social networks.",
            "venue": "Journal of Geriatric Psychiatry",
            "citation_count": 120,
        },
    ]
    with patch(
        "apps.api.features.retrieval.relevance.qualis_service.apply_relevance_boost", side_effect=lambda s, p: (s, {})
    ):
        ranked, stats = filter_and_rank_papers(
            papers,
            topics=["social capital", "social networks", "profile modeling"],
            research_area="Recommender Systems",
            min_score=0.22,
        )
    assert stats["kept"] == 1
    assert "recommender" in ranked[0]["title"].lower()
    assert ranked[0]["domain_alignment_passes"] is True


def test_build_research_context_merges_topics_and_area():
    context = build_research_context(
        research_area="Recommender Systems",
        topics=["social capital"],
        learned_topics=["graph neural networks"],
    )
    assert context is not None
    assert "recommender" in context.area_tokens
    assert "social" in context.topic_tokens
    assert "computer_science" in context.expected_fields


def test_compute_context_alignment_wrapper_accepts_topics():
    paper = {
        "title": "Social capital in rural communities",
        "abstract": "A qualitative sociological study.",
        "venue": "American Journal of Sociology",
    }
    alignment = compute_context_alignment(
        paper,
        research_area="Recommender Systems",
        topics=["social capital"],
    )
    assert alignment.passes is False
