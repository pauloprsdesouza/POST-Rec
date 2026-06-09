"""LLM facet critic (Idea Novelty Checker–style per-facet comparison)."""

from packages.postrec_core.prompts.shared_grounding import GROUNDING_CONSTITUTION

FACET_CRITIC_USER_TEMPLATE = f"""Compare this research proposal's facet deltas against the closest literature facets.

{GROUNDING_CONSTITUTION}

Retrieved papers (evidence only):
{{papers_context}}

Proposal facet deltas:
{{facet_deltas_json}}

Closest literature facet statements per type:
{{closest_matches_json}}

## Verification protocol
For each facet (problem, method, data, evaluation):
1. Locate the closest corpus statement and its source paper_id
2. Judge whether the proposal facet is genuinely novel vs that statement
3. Penalize facets that paraphrase a single paper without extension

Return JSON:
{{{{
  "per_facet": {{{{
    "problem": {{{{"novel": true, "novelty_0_100": 0, "rationale": "short", "source_paper_id": "P1"}}}},
    "method": {{{{"novel": true, "novelty_0_100": 0, "rationale": "short", "source_paper_id": "P1"}}}},
    "data": {{{{"novel": true, "novelty_0_100": 0, "rationale": "short", "source_paper_id": "P1"}}}},
    "evaluation": {{{{"novel": true, "novelty_0_100": 0, "rationale": "short", "source_paper_id": "P1"}}}}
  }}}},
  "false_novel_risk": "low|medium|high",
  "overall_novelty_0_100": 0,
  "citations_grounded": true
}}}}

Mark novel=false if the facet largely repeats a single paper without extension.
Set citations_grounded=false if any referenced paper is not in the retrieved list."""
