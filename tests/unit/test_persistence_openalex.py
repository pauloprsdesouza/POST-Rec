"""Tests for OpenAlex metadata persistence."""

from apps.api.features.retrieval.persistence import merge_paper_metadata
from apps.api.shared.models import SourceDocument


def test_merge_paper_metadata_includes_openalex_fields():
    doc = SourceDocument(
        source="openalex",
        title="Test paper",
        metadata_={},
    )
    merge_paper_metadata(
        doc,
        {
            "openalex_field": "Computer Science",
            "openalex_fwci": 1.8,
            "is_open_access": True,
            "openalex_keywords": ["recommender systems"],
        },
    )
    assert doc.metadata_["openalex_field"] == "Computer Science"
    assert doc.metadata_["openalex_fwci"] == 1.8
    assert doc.metadata_["is_open_access"] is True
    assert doc.metadata_["openalex_keywords"] == ["recommender systems"]
