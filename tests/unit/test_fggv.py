"""Unit tests for facet extraction and FGGV scoring."""

from packages.postrec_core.facets.extraction import extract_paper_facets
from packages.postrec_core.facets.facet_map import build_literature_facet_map
from packages.postrec_core.facets.gap_facet_alignment import compute_gap_facet_alignment
from packages.postrec_core.scoring.facet_grounded_ranking import compute_facet_novelty_index, compute_fggv_score


def test_extract_paper_facets_from_abstract():
    paper = {
        "title": "GNN Rec",
        "abstract": "However scalability remains unclear. We use graph neural networks on MovieLens.",
    }
    facets = extract_paper_facets(paper)
    assert facets["problem"]
    assert "graph neural" in facets["method"].lower() or "gnn" in facets["method"].lower()


def test_facet_novelty_higher_for_distinct_proposal():
    papers = [
        {"title": "A", "abstract": "Graph convolution for recommendation on MovieLens with NDCG."},
        {"title": "B", "abstract": "Graph convolution baseline with standard metrics."},
    ]
    facet_map = build_literature_facet_map(papers)
    distinct = {
        "facet_deltas": {
            "problem": "Federated cold-start recommendation under privacy",
            "method": "Differential privacy subgraph aggregation",
            "data": "Cross-silo e-commerce logs",
            "evaluation": "Privacy budget vs NDCG tradeoff curves",
        }
    }
    generic = {
        "facet_deltas": {
            "problem": "Graph recommendation",
            "method": "Graph convolution",
            "data": "MovieLens",
            "evaluation": "NDCG",
        }
    }
    fni_distinct, _, _ = compute_facet_novelty_index(distinct, facet_map)
    fni_generic, _, _ = compute_facet_novelty_index(generic, facet_map)
    assert fni_distinct > fni_generic


def test_gap_alignment_with_aligned_gaps():
    gap_matrix = {
        "gaps": [
            {
                "gap": "Scalable subgraph training",
                "suggested_direction": "Localized sampling",
            }
        ]
    }
    proposal = {
        "facet_deltas": {
            "problem": "Large-scale graphs",
            "method": "Localized subgraph training",
            "data": "benchmark",
            "evaluation": "NDCG",
        },
        "aligned_gaps": ["Scalable subgraph training"],
        "novelty_delta": "Subgraph training extension",
    }
    score = compute_gap_facet_alignment(proposal, gap_matrix)
    assert score > 0.3


def test_fggv_score_blends_signals():
    score = compute_fggv_score(
        verified_final_score=70.0,
        facet_novelty_index=0.8,
        gap_alignment_score=0.7,
        document_novelty_verified=0.6,
    )
    assert 65 <= score <= 85
