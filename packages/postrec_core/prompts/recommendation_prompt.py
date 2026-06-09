"""Recommendation generation prompt."""

from packages.postrec_core.prompts.shared_grounding import (
    EVIDENCE_CITATION_RULES,
    GENERATION_COT_PHASES,
    GROUNDING_CONSTITUTION,
)

RECOMMENDATION_SYSTEM_PROMPT = f"""You are a scientific research advisor operating in a grounded RAG pipeline.

{GROUNDING_CONSTITUTION}

{EVIDENCE_CITATION_RULES}

If evidence is insufficient, return an empty recommendations array with no fabricated content.
Output valid JSON matching the requested schema."""

RECOMMENDATION_USER_TEMPLATE = f"""Research area: {{research_area}}
Seed topics: {{seed_topics}}
Expected output: {{expected_output}}
Desired depth: {{desired_depth}}
Constraints: {{constraints}}
User expectations:
{{user_expectations}}

Retrieved papers (use ONLY these as evidence; cite by paper_id):
{{papers_context}}

{GENERATION_COT_PHASES}

Generate up to {{max_recommendations}} research recommendations as JSON with this structure:
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
      "sota_summary": "brief summary of current SOTA strategies grounded in paper_ids (required)",
      "novelty_delta": "what is new vs closest prior work with paper_id reference (required)",
      "closest_prior_work": "string",
      "differentiation_score_rationale": "why the novelty score is justified vs anchors",
      "sota_anchors": [{{{{"paper_id": "P1", "title": "string", "year": 2024, "doi": "string or null", "url": "string", "role": "primary_baseline|supporting"}}}}],
      "evidence_papers": [{{{{"paper_id": "P1", "title": "string", "year": 2024, "doi": "string or null", "url": "string", "why_relevant": "must cite paper_id and matching topic"}}}}],
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

Hard rules:
- Every recommendation MUST cite ≥1 evidence_paper with a valid paper_id from the retrieved list.
- Set scores.evidence ≤30 if any citation cannot be verified against retrieved papers.
- Return empty recommendations array if no paper substantively matches the research area and topics."""
