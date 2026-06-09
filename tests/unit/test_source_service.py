"""Tests for source document enrichment."""

import uuid
from unittest.mock import MagicMock

from apps.api.features.recommendations.sources import enrich_evidence_papers


def _mock_doc(*, doi=None, title="Sample Paper", source="openalex", citations=42, metadata=None):
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.doi = doi
    doc.title = title
    doc.source = source
    doc.citation_count = citations
    doc.venue = "NeurIPS"
    doc.abstract = "An abstract."
    doc.url = "https://example.org/paper"
    doc.metadata_ = metadata
    return doc


def test_enrich_evidence_matches_by_doi():
    doc = _mock_doc(doi="10.1234/test", title="Different title")
    evidence = [{"title": "Cited title", "doi": "10.1234/test", "why_relevant": "Core method"}]

    enriched = enrich_evidence_papers(evidence, [doc])

    assert len(enriched) == 1
    assert enriched[0]["matched_in_catalog"] is True
    assert enriched[0]["retrieval_source"] == "openalex"
    assert enriched[0]["citation_count"] == 42
    assert enriched[0]["why_relevant"] == "Core method"


def test_enrich_evidence_matches_by_title_when_no_doi():
    doc = _mock_doc(title="Attention Is All You Need")
    evidence = [{"title": "Attention Is All You Need", "year": 2017}]

    enriched = enrich_evidence_papers(evidence, [doc])

    assert enriched[0]["matched_in_catalog"] is True
    assert enriched[0]["venue"] == "NeurIPS"


def test_enrich_evidence_unmatched_still_returns_citation():
    evidence = [{"title": "Unknown Paper", "doi": "10.9999/none", "why_relevant": "Related"}]

    enriched = enrich_evidence_papers(evidence, [])

    assert enriched[0]["matched_in_catalog"] is False
    assert enriched[0]["retrieval_source"] is None
    assert enriched[0]["why_relevant"] == "Related"


def test_enrich_evidence_includes_qualis_from_matched_catalog_doc():
    doc = _mock_doc(
        doi="10.1234/test",
        metadata={"qualis_estrato": "a1", "qualis_boost": 0.08, "qualis_period": "2021-2024"},
    )
    evidence = [{"title": "Cited title", "doi": "10.1234/test"}]

    enriched = enrich_evidence_papers(evidence, [doc])

    assert enriched[0]["qualis_estrato"] == "A1"
    assert enriched[0]["qualis_boost"] == 0.08
    assert enriched[0]["qualis_period"] == "2021-2024"


def test_enrich_evidence_includes_relevance_score_from_metadata():
    doc = _mock_doc(
        doi="10.1234/test",
        metadata={"llm_relevance_score": 0.82},
    )
    evidence = [{"title": "Cited title", "doi": "10.1234/test", "why_relevant": "Core method"}]

    enriched = enrich_evidence_papers(evidence, [doc])

    assert enriched[0]["relevance_score"] == 0.82


def test_enrich_evidence_omits_qualis_when_unmatched():
    evidence = [{"title": "Unknown Paper", "doi": "10.9999/none"}]

    enriched = enrich_evidence_papers(evidence, [])

    assert "qualis_estrato" not in enriched[0]
    assert "qualis_boost" not in enriched[0]
