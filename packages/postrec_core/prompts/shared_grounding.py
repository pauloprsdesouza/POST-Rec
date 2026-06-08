"""Shared grounding constraints and reasoning scaffolds for LLM prompts."""

# Instruction hierarchy (highest priority first): grounding → task → format.
GROUNDING_CONSTITUTION = """## Grounding constitution (non-negotiable)
1. Use ONLY information from the retrieved papers listed below. Never invent papers, DOIs, authors, venues, or findings.
2. Every cited paper MUST appear verbatim in the retrieved list (match by paper_id and/or title).
3. If retrieved evidence is insufficient for the research scope, return empty arrays — do NOT fabricate ideas.
4. Scores and claims must be traceable to specific paper_id(s) in the evidence list.
5. When uncertain about a paper's relevance, exclude it rather than assume relevance."""

EVIDENCE_CITATION_RULES = """## Citation rules
- Reference papers by paper_id (e.g. P3) in evidence_papers.why_relevant and sota_anchors.
- evidence_papers and sota_anchors MUST only include papers from the retrieved list.
- Do not cite papers mentioned only in your training data."""

GENERATION_COT_PHASES = """## Reasoning protocol (complete internally, then output JSON only)
PHASE 1 — Scope audit: For each seed topic, identify which paper_ids (if any) directly address it.
PHASE 2 — Evidence gate: If fewer than 2 papers substantively match the research area + topics, return an empty recommendations array.
PHASE 3 — Synthesis: Build each recommendation ONLY from papers that passed PHASE 1.
PHASE 4 — Self-verification: Confirm every evidence_papers/sota_anchors entry maps to a retrieved paper_id; remove any that do not."""

LANDSCAPE_COT_PHASES = """## Reasoning protocol (complete internally, then output JSON only)
PHASE 1 — Per-paper scan: For each paper_id, note methods, datasets, metrics, and stated limitations.
PHASE 2 — Topic filter: Exclude findings from papers that do not match the research area or seed topics.
PHASE 3 — Aggregation: Summarize only patterns supported by ≥2 relevant papers or one high-relevance paper.
PHASE 4 — Self-check: Every item in methods/datasets/metrics/open_problems must trace to a paper_id."""
