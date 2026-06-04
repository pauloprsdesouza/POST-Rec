"""Unit tests for novelty verification helpers."""

from packages.postrec_core.scoring.novelty_verification import (
    blend_novelty_verified,
    claim_overlap_novelty,
    compute_sota_fit,
    embedding_novelty,
    proposal_text,
)


def test_proposal_text_concatenates_fields():
    text = proposal_text(
        {
            "title": "Title",
            "research_gap": "Gap",
            "novelty_delta": "Delta",
        }
    )
    assert "Title" in text
    assert "Gap" in text
    assert "Delta" in text


def test_claim_overlap_novelty_higher_when_distinct():
    proposal = "quantum graph neural networks for drug discovery"
    corpus = ["classical support vector machines for image classification"]
    score = claim_overlap_novelty(proposal, corpus)
    assert score > 0.7


def test_embedding_novelty_increases_with_distance():
    proposal = [1.0, 0.0]
    close = embedding_novelty(proposal, [[0.99, 0.01]])
    far = embedding_novelty(proposal, [[0.0, 1.0]])
    assert far > close


def test_blend_novelty_verified_without_llm():
    blended = blend_novelty_verified(0.8, 0.6, None, llm_blend=0.35)
    assert 0.65 <= blended <= 0.75


def test_compute_sota_fit_with_recent_anchor():
    recommendation = {
        "sota_summary": "Recent transformer methods dominate this area with strong benchmarks.",
        "sota_anchors": [{"title": "Recent Paper", "role": "primary_baseline"}],
    }
    papers = [{"title": "Recent Paper", "tier": "sota_recent"}]
    fit = compute_sota_fit(recommendation, papers)
    assert fit > 0.4
