"""Unit tests for paper tier classification."""

from packages.postrec_core.retrieval.paper_tier import (
    PAPER_TIER_PERIPHERAL,
    PAPER_TIER_SEMINAL,
    PAPER_TIER_SOTA_RECENT,
    classify_paper_tier,
    current_year,
    tag_paper_tiers,
)


def test_classify_recent_paper_as_sota_recent():
    tier = classify_paper_tier({"year": current_year(), "citation_count": 5})
    assert tier == PAPER_TIER_SOTA_RECENT


def test_classify_high_citation_old_paper_as_seminal():
    tier = classify_paper_tier({"year": 2010, "citation_count": 120})
    assert tier == PAPER_TIER_SEMINAL


def test_classify_low_signal_paper_as_peripheral():
    tier = classify_paper_tier({"year": 2010, "citation_count": 3})
    assert tier == PAPER_TIER_PERIPHERAL


def test_tag_paper_tiers_attaches_tier_field():
    papers = [{"title": "A", "year": current_year(), "citation_count": 1}]
    tagged = tag_paper_tiers(papers)
    assert tagged[0]["tier"] == PAPER_TIER_SOTA_RECENT
