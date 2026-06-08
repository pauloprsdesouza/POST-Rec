"""Tests for persisting article-validation scores on SourceDocument metadata."""

import uuid
from unittest.mock import MagicMock

from apps.api.features.recommendations.article_validation import article_validation_service
from apps.api.features.retrieval.persistence import (
    merge_validation_metadata,
    persist_article_validation_scores,
)
from apps.api.shared.models import SourceDocument


def test_merge_validation_metadata_writes_scores():
    doc = SourceDocument(source="openalex", title="Paper")
    merge_validation_metadata(
        doc,
        {
            "llm_relevance_score": 0.82,
            "relevance_score": 0.45,
            "llm_passes_validation": True,
            "llm_matched_topics": ["recsys"],
            "llm_match_rationale": "title overlap",
            "llm_avoided_topic_hit": False,
        },
        run_id="run-abc",
        method="llm",
    )
    assert doc.metadata_["article_validation_method"] == "llm"
    assert doc.metadata_["article_validated_at_run_id"] == "run-abc"
    assert doc.metadata_["llm_relevance_score"] == 0.82
    assert doc.metadata_["deterministic_relevance_score"] == 0.45
    assert doc.metadata_["llm_passes_validation"] is True
    assert doc.metadata_["llm_matched_topics"] == ["recsys"]


def test_persist_article_validation_scores_updates_linked_documents():
    doc_id = uuid.uuid4()
    doc = SourceDocument(id=doc_id, source="openalex", title="Paper")
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [doc]

    updated = persist_article_validation_scores(
        db,
        [
            {
                "source_document_id": str(doc_id),
                "llm_relevance_score": 0.9,
                "relevance_score": 0.3,
                "llm_passes_validation": True,
            }
        ],
        run_id="run-1",
        method="deterministic",
    )

    assert updated == 1
    assert doc.metadata_["llm_relevance_score"] == 0.9
    db.commit.assert_called_once()


def test_deterministic_filter_scores_filtered_out_papers():
    papers = [
        {
            "paper_id": "P1",
            "source_document_id": str(uuid.uuid4()),
            "title": "Graph neural networks for recommender systems",
            "abstract": "GNN collaborative filtering study.",
        },
        {
            "paper_id": "P2",
            "source_document_id": str(uuid.uuid4()),
            "title": "Medieval crop rotation",
            "abstract": "Historical agriculture.",
        },
    ]
    kept, stats, scored_all = article_validation_service._deterministic_filter(
        papers,
        research_area="Recommender Systems",
        seed_topics=["recommender systems"],
        avoided_topics=None,
        min_score=0.22,
        min_valid=1,
    )
    assert stats["kept"] == 1
    assert len(scored_all) == 2
    assert scored_all[1]["llm_passes_validation"] is False
