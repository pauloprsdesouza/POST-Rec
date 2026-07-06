"""Prompt for generating implementation roadmaps from approved recommendations."""

PROJECT_ROADMAP_SYSTEM_PROMPT = """You are a scientific research mentor helping a researcher turn an approved idea into a published paper.

Provide structured, actionable guidance — not automation. Tasks should be specific to the recommendation content.
Ground tasks in the recommendation fields and evidence paper IDs provided.
Do not invent paper IDs or datasets not mentioned in the input.
Output valid JSON matching the requested schema."""

PROJECT_ROADMAP_USER_TEMPLATE = """Research area: {research_area}
Academic level: {academic_level}
Scientific writing experience: {writing_experience}
Locale for text: {locale}

Approved recommendation:
Title: {title}
Research gap: {research_gap}
Research question: {research_question}
Hypothesis: {hypothesis}
Proposed method: {proposed_method}
Experimental plan: {experimental_plan}
Expected contribution: {expected_contribution}
Datasets: {datasets}
Evaluation metrics: {evaluation_metrics}
Risks: {risks}
Evidence papers: {evidence_papers}

Generate an implementation roadmap with exactly 6 phases in this order:
1. Foundation & literature
2. Study design
3. Execution
4. Analysis & validation
5. Writing
6. Publication

Each phase should have 4 to 6 tasks. Each task must include:
- title (imperative, actionable)
- description (2-3 sentences)
- guidance (why this matters for THIS recommendation)
- effort: "S", "M", or "L"
- linked_fields: array of recommendation field names this task draws from (e.g. "proposed_method")
- linked_paper_ids: array of paper_id strings from evidence papers, or empty
- checklist: optional array of 2-4 short sub-steps

Return JSON:
{{
  "phases": [
    {{
      "title": "string",
      "description": "string",
      "tasks": [
        {{
          "title": "string",
          "description": "string",
          "guidance": "string",
          "effort": "S|M|L",
          "linked_fields": ["string"],
          "linked_paper_ids": ["P1"],
          "checklist": ["string"]
        }}
      ]
    }}
  ]
}}"""
