"""Recommendation generation prompt."""

RECOMMENDATION_SYSTEM_PROMPT = """You are a scientific research advisor. Generate structured research recommendations
based ONLY on the retrieved papers provided. Do not invent DOIs, authors, venues, or papers.
Only reference papers from the provided evidence list. Output valid JSON matching the schema."""

RECOMMENDATION_USER_TEMPLATE = """Research area: {research_area}
Seed topics: {seed_topics}
Expected output: {expected_output}
Desired depth: {desired_depth}
Constraints: {constraints}
User expectations:
{user_expectations}

Retrieved papers (use ONLY these as evidence):
{papers_context}

Generate {max_recommendations} research recommendations as JSON with this structure:
{{
  "recommendations": [
    {{
      "title": "string",
      "technique_name": "string",
      "research_gap": "string",
      "research_question": "string",
      "hypothesis": "string",
      "proposed_method": "string",
      "related_work_summary": "string",
      "sota_summary": "brief summary of current SOTA strategies (required)",
      "novelty_delta": "what is new vs closest prior work (required)",
      "closest_prior_work": "string",
      "differentiation_score_rationale": "why the novelty score is justified vs anchors",
      "sota_anchors": [{{"title": "string", "year": 2024, "doi": "string or null", "url": "string", "role": "primary_baseline|supporting"}}],
      "evidence_papers": [{{"title": "string", "year": 2024, "doi": "string or null", "url": "string", "why_relevant": "string"}}],
      "datasets": ["string"],
      "evaluation_metrics": ["string"],
      "experimental_plan": "string",
      "risks": ["string"],
      "expected_contribution": "string",
      "confidence_level": "low|medium|high",
      "scores": {{
        "relevance": 0-100,
        "novelty": 0-100,
        "evidence": 0-100,
        "feasibility": 0-100,
        "trend": 0-100,
        "publication_potential": 0-100,
        "strategic_fit": 0-100,
        "final_score": 0-100
      }}
    }}
  ]
}}"""
