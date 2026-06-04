"""LLM facet critic (Idea Novelty Checker–style per-facet comparison)."""

FACET_CRITIC_USER_TEMPLATE = """Compare this research proposal's facet deltas against the closest literature facets.

Retrieved papers (evidence only):
{papers_context}

Proposal facet deltas:
{facet_deltas_json}

Closest literature facet statements per type:
{closest_matches_json}

For each facet (problem, method, data, evaluation), judge whether the proposal facet is genuinely novel
vs the closest corpus statements. Return JSON:
{{
  "per_facet": {{
    "problem": {{"novel": true, "novelty_0_100": 0-100, "rationale": "short"}},
    "method": {{"novel": true, "novelty_0_100": 0-100, "rationale": "short"}},
    "data": {{"novel": true, "novelty_0_100": 0-100, "rationale": "short"}},
    "evaluation": {{"novel": true, "novelty_0_100": 0-100, "rationale": "short"}}
  }},
  "false_novel_risk": "low|medium|high",
  "overall_novelty_0_100": 0-100
}}

Mark novel=false if the facet largely repeats a single paper without extension."""
