"""Tests for recommendation validator."""

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.validation.recommendation_validator import (
    validate_recommendation,
    verify_citations,
)


def test_verify_citations_flags_unknown_title():
    papers = [{"title": "Known Paper", "doi": "10.1/abc"}]
    rec = {"evidence_papers": [{"title": "Unknown Paper", "doi": None}]}
    issues = verify_citations(rec, papers)
    assert any("Unknown Paper" in issue for issue in issues)


def test_validate_good_sota_proposal():
    papers = [{"title": "Recent Paper", "year": 2025, "tier": "sota_recent", "doi": "10.1/x"}]
    rec = {
        "title": "Proposal",
        "sota_summary": "Recent methods dominate.",
        "novelty_delta": "We extend training efficiency.",
        "closest_prior_work": "Recent Paper",
        "sota_anchors": [{"title": "Recent Paper", "year": 2025, "doi": "10.1/x"}],
        "evidence_papers": [{"title": "Recent Paper", "year": 2025, "doi": "10.1/x"}],
    }
    result = validate_recommendation(rec, papers, mode=RunMode.SOTA)
    assert result.valid is True
    assert result.publication_status == "published"


def test_validate_weak_proposal_needs_refinement_in_sota_mode():
    papers = [{"title": "Recent Paper", "year": 2025, "tier": "sota_recent"}]
    rec = {
        "title": "Weak",
        "evidence_papers": [{"title": "Missing Paper"}],
    }
    result = validate_recommendation(rec, papers, mode=RunMode.SOTA)
    assert result.valid is False
    assert result.publication_status == "needs_refinement"
