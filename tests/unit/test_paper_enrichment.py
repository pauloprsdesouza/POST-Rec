"""Tests for paper enrichment."""

from packages.postrec_core.retrieval.paper_enrichment import enrich_paper_metadata, extract_limitations


def test_extract_limitations_from_abstract():
    abstract = "Our method works well. However, scalability remains unclear. Future work includes larger benchmarks."
    limits = extract_limitations(abstract)
    assert len(limits) >= 1


def test_enrich_paper_metadata_adds_labels():
    enriched = enrich_paper_metadata(
        {
            "title": "Graph neural recommender with transformers",
            "abstract": "However, evaluation remains limited. Future work on benchmarks.",
        }
    )
    meta = enriched["metadata"]
    assert meta.get("limitations") or meta.get("methods")
