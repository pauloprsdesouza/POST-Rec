"""Threshold rationale for article LLM validation."""

import json
from pathlib import Path

from apps.api.features.retrieval.relevance import compute_relevance_score
from apps.api.shared.settings import Settings

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "golden_eval_topics.json"


def test_article_llm_min_relevance_score_default_is_semantic_rubric():
    """0.5 is the LLM rubric midpoint; lexical scores on golden fixtures are much lower."""
    assert Settings().article_llm_min_relevance_score == 0.5


def test_golden_eval_fixture_papers_score_low_on_lexical_relevance():
    """Golden fixture titles/abstracts are minimal stubs — not used to tune the LLM threshold."""
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    lexical_threshold = Settings().retrieval_min_relevance_score

    for topic in payload["topics"]:
        for paper in topic["papers"]:
            score = compute_relevance_score(
                paper,
                topics=topic["seed_topics"],
                research_area=topic["research_area"],
            )
            assert score < lexical_threshold or score < Settings().article_llm_min_relevance_score
