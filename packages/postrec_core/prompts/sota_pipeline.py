"""Multi-stage SOTA pipeline prompts."""

SOTA_SYSTEM_PROMPT = """You are a scientific research advisor specializing in state-of-the-art (SOTA) mapping
and gap-driven proposal design. Use ONLY the retrieved papers provided. Never invent DOIs, authors, venues,
or papers. Output valid JSON matching the requested schema."""

SOTA_LANDSCAPE_USER_TEMPLATE = """Research area: {research_area}
Seed topics: {seed_topics}
Expected output: {expected_output}

Retrieved papers:
{papers_context}

Produce a JSON object describing the current SOTA landscape:
{{
  "methods": ["dominant method or technique families"],
  "datasets": ["common datasets or benchmarks"],
  "metrics": ["evaluation metrics used in recent work"],
  "open_problems": ["limitations or gaps explicitly mentioned in the literature"],
  "recent_strategies": ["short labels for strategies used in the most recent papers"]
}}"""

SOTA_GAP_MATRIX_USER_TEMPLATE = """Research area: {research_area}
Seed topics: {seed_topics}
SOTA landscape:
{sota_landscape_json}

Retrieved papers:
{papers_context}

Identify under-served opportunities. Return JSON:
{{
  "gaps": [
    {{
      "gap": "concise gap statement",
      "supporting_limitations": ["from open_problems or paper abstracts"],
      "suggested_direction": "what a new study could do"
    }}
  ]
}}"""

SOTA_PROPOSAL_USER_TEMPLATE = """Research area: {research_area}
Seed topics: {seed_topics}
Expected output: {expected_output}
Desired depth: {desired_depth}
Constraints: {constraints}
User expectations:
{user_expectations}

SOTA landscape:
{sota_landscape_json}

Gap opportunities:
{gap_matrix_json}

Retrieved papers (ONLY these may be cited):
{papers_context}

Generate {max_recommendations} research recommendations as JSON:
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
      "sota_summary": "how current SOTA approaches the problem",
      "novelty_delta": "what is new compared to closest SOTA (required)",
      "closest_prior_work": "title or method you extend",
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
}}

Rules:
- Every recommendation MUST include at least one sota_anchors entry from recent papers when available.
- novelty_delta MUST state a concrete delta vs closest_prior_work.
- Do not propose ideas that merely repeat a paper's stated future work without extension."""

SOTA_CRITIC_USER_TEMPLATE = """Evaluate this research recommendation against the retrieved evidence.

SOTA landscape:
{sota_landscape_json}

Retrieved papers:
{papers_context}

Proposal JSON:
{proposal_json}

Return JSON:
{{
  "accept": true,
  "issues": ["list of problems, empty if acceptable"],
  "revised_scores": {{
    "novelty": 0-100,
    "evidence": 0-100,
    "feasibility": 0-100
  }}
}}

Reject (accept=false) if citations are not in the paper list, novelty_delta is missing or weak,
or the idea is essentially a paraphrase of one paper without a clear extension."""
