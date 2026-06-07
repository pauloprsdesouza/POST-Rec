"""FGGV-specific prompts extending the SOTA pipeline."""

FGGV_PROPOSAL_USER_TEMPLATE = """Research area: {research_area}
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

Literature facet saturation (higher = more crowded):
{facet_saturation_json}

Under-served facets to prioritize (lower saturation — target these for novelty):
{underserved_facets_json}

Retrieved papers (ONLY these may be cited):
{papers_context}

Generate {max_recommendations} research recommendations using Facet-Grounded Gap Verification (FGGV).
Each idea MUST declare explicit per-facet deltas and gap alignment.

Return JSON:
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
      "novelty_delta": "document-level summary of what is new",
      "facet_deltas": {{
        "problem": "what problem facet is new vs corpus",
        "method": "what method facet is new vs corpus",
        "data": "what data/benchmark facet is new vs corpus",
        "evaluation": "what evaluation facet is new vs corpus"
      }},
      "aligned_gaps": ["gap statement(s) from gap matrix this proposal addresses"],
      "closest_prior_work": "title or method you extend",
      "differentiation_score_rationale": "why facet deltas are novel vs anchors",
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
- facet_deltas MUST differ from saturated facets in the literature map where possible.
- aligned_gaps MUST reference at least one gap from the gap matrix.
- Do not repeat a single paper's future work without a multi-facet extension.
- Every recommendation MUST include at least one sota_anchors entry from recent papers when available."""
