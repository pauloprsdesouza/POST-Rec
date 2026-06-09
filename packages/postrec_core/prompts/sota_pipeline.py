"""Multi-stage SOTA pipeline prompts."""

from packages.postrec_core.prompts.shared_grounding import (
    EVIDENCE_CITATION_RULES,
    GENERATION_COT_PHASES,
    GROUNDING_CONSTITUTION,
    LANDSCAPE_COT_PHASES,
)

SOTA_SYSTEM_PROMPT = f"""You are a scientific research advisor specializing in state-of-the-art (SOTA) mapping
and gap-driven proposal design in a grounded RAG pipeline.

{GROUNDING_CONSTITUTION}

{EVIDENCE_CITATION_RULES}

Never proceed to synthesis when retrieved papers do not match the research scope.
Output valid JSON matching the requested schema."""

SOTA_LANDSCAPE_USER_TEMPLATE = f"""Research area: {{research_area}}
Seed topics: {{seed_topics}}
Expected output: {{expected_output}}

Retrieved papers (cite by paper_id in reasoning):
{{papers_context}}

{LANDSCAPE_COT_PHASES}

Produce a JSON object describing the current SOTA landscape (only from relevant papers):
{{{{
  "methods": ["dominant method families with paper_id hints, e.g. 'GNN collaborative filtering (P2, P5)'"],
  "datasets": ["common datasets or benchmarks"],
  "metrics": ["evaluation metrics used in recent work"],
  "open_problems": ["limitations explicitly stated in paper abstracts"],
  "recent_strategies": ["short labels for strategies in the most recent relevant papers"],
  "relevant_paper_ids": ["P1", "P2"],
  "insufficient_evidence": false
}}}}

Set insufficient_evidence=true and leave arrays empty if no paper substantively matches the research area and topics."""

SOTA_GAP_MATRIX_USER_TEMPLATE = f"""Research area: {{research_area}}
Seed topics: {{seed_topics}}
SOTA landscape:
{{sota_landscape_json}}

Retrieved papers:
{{papers_context}}

{LANDSCAPE_COT_PHASES}

Identify under-served opportunities grounded ONLY in relevant papers. Return JSON:
{{{{
  "gaps": [
    {{{{
      "gap": "concise gap statement",
      "supporting_limitations": ["from open_problems or paper abstracts with paper_id"],
      "supporting_paper_ids": ["P1"],
      "suggested_direction": "what a new study could do"
    }}}}
  ],
  "insufficient_evidence": false
}}}}

Return empty gaps array if insufficient_evidence is true in the landscape or no paper matches the scope."""

SOTA_PROPOSAL_USER_TEMPLATE = f"""Research area: {{research_area}}
Seed topics: {{seed_topics}}
Expected output: {{expected_output}}
Desired depth: {{desired_depth}}
Constraints: {{constraints}}
User expectations:
{{user_expectations}}

SOTA landscape:
{{sota_landscape_json}}

Gap opportunities:
{{gap_matrix_json}}

Retrieved papers (ONLY these may be cited; use paper_id):
{{papers_context}}

{GENERATION_COT_PHASES}

Generate up to {{max_recommendations}} research recommendations as JSON:
{{{{
  "recommendations": [
    {{{{
      "title": "string",
      "technique_name": "string",
      "research_gap": "string",
      "research_question": "string",
      "hypothesis": "string",
      "proposed_method": "string",
      "related_work_summary": "string",
      "sota_summary": "how current SOTA approaches the problem with paper_id references",
      "novelty_delta": "what is new compared to closest SOTA (required)",
      "closest_prior_work": "title or method you extend",
      "differentiation_score_rationale": "why the novelty score is justified vs anchors",
      "sota_anchors": [{{{{"paper_id": "P1", "title": "string", "year": 2024, "doi": "string or null", "url": "string", "role": "primary_baseline|supporting"}}}}],
      "evidence_papers": [{{{{"paper_id": "P1", "title": "string", "year": 2024, "doi": "string or null", "url": "string", "why_relevant": "string"}}}}],
      "datasets": ["string"],
      "evaluation_metrics": ["string"],
      "experimental_plan": "string",
      "risks": ["string"],
      "expected_contribution": "string",
      "confidence_level": "low|medium|high",
      "scores": {{{{
        "relevance": 0-100,
        "novelty": 0-100,
        "evidence": 0-100,
        "feasibility": 0-100,
        "trend": 0-100,
        "publication_potential": 0-100,
        "strategic_fit": 0-100,
        "final_score": 0-100
      }}}}
    }}}}
  ]
}}}}

Rules:
- Every recommendation MUST include at least one sota_anchors entry from recent papers when available.
- novelty_delta MUST state a concrete delta vs closest_prior_work with paper_id evidence.
- Do not propose ideas that merely repeat a paper's stated future work without extension.
- Return empty recommendations if landscape.insufficient_evidence is true or gap_matrix has no gaps."""

SOTA_CRITIC_USER_TEMPLATE = f"""Evaluate this research recommendation against the retrieved evidence.

{GROUNDING_CONSTITUTION}

SOTA landscape:
{{sota_landscape_json}}

Retrieved papers:
{{papers_context}}

Proposal JSON:
{{proposal_json}}

## Verification protocol
1. Check every evidence_papers/sota_anchors entry exists in retrieved papers (by paper_id or title).
2. Verify novelty_delta cites real evidence from retrieved papers.
3. Confirm the idea addresses the research scope, not an unrelated domain.
4. Reject if any citation is hallucinated or novelty_delta is missing/weak.

Return JSON:
{{{{
  "accept": true,
  "issues": ["list of problems, empty if acceptable"],
  "revised_scores": {{{{
    "novelty": 0-100,
    "evidence": 0-100,
    "feasibility": 0-100
  }}}},
  "citation_verified": true,
  "topic_alignment": "high|medium|low"
}}}}

Reject (accept=false) if citations are not in the paper list, novelty_delta is missing or weak,
the idea is essentially a paraphrase of one paper without a clear extension, or topic_alignment is low."""
