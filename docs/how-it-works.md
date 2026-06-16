# POST-Rec: System Overview and Methodology

## 1. Abstract

POST-Rec is a research ideation system that generates literature-grounded research ideas from user-provided topics. It combines hybrid retrieval over scholarly articles, a multi-stage state-of-the-art (SOTA) analysis pipeline, and an experimental Facet-Grounded Gap Verification (FGGV) method for facet-level novelty and gap alignment. This document describes how POST-Rec works end-to-end, what “SOTA-grounded” means in practice, which articles are considered part of the SOTA set, how FGGV extends the baseline pipeline, and how the system is evaluated. The goal is to provide reviewers and collaborators with a transparent, citable description aligned with common Elsevier-style journal templates.

## 2. Introduction

### 2.1 Problem setting

Researchers increasingly use large language models (LLMs) and retrieval-augmented generation (RAG) systems to explore research directions. However, many tools:

- provide ideas that are weakly grounded in actual literature,
- fail to distinguish genuinely novel ideas from already-solved problems,
- do not expose enough detail for reviewers to understand how “state of the art” (SOTA) is defined.

POST-Rec addresses these issues by:

- retrieving and normalizing articles from open scholarly catalogs,
- explicitly constructing a SOTA subset of the literature per topic,
- generating ideas through a multi-stage pipeline,
- verifying novelty and SOTA alignment at both document and facet levels.

### 2.2 Contributions

From a methods perspective, POST-Rec offers:

- **SOTA-grounded pipeline**: a configurable definition of SOTA based on recency, citations, and domain filters, used consistently across modes.
- **Facet-Grounded Gap Verification (FGGV)**: an extension over the SOTA pipeline that introduces facet maps, gap–facet alignment, facet-level novelty indices, and diversity-aware selection [FGGV Doc].
- **Transparent scoring and evaluation**: explicit metrics and endpoints for offline and online analysis [Analysis Spec].

Throughout this document we refer to:

- **SOTA mode** as the baseline multi-stage pipeline, and
- **FGGV mode** as the proposed method that augments SOTA with facet-grounded verification.

## 3. Background and Related Work

### 3.1 Literature-grounded ideation systems

Recent work has proposed LLM-based research ideation agents that combine retrieval over papers with idea generation and ranking. Representative examples include:

- **Si et al. (ICLR 2025)** — LLM research ideation agent with retrieval over papers and human-rated originality, without explicit facet maps or gap matrices [Si25].
- **Scideator** — a system that recombines method and problem facets extracted from a paper pool, with facet-level novelty checks but weaker explicit gap alignment [Sci].
- **Idea Novelty Checker** — a pipeline that retrieves documents, re-ranks them, and applies per-facet LLM comparisons to detect novelty, using expert-labeled in-context examples [INC].
- **NOVA / ResearchAgent-style systems** — multi-agent or planning-based systems that iteratively expand knowledge graphs or citation graphs, with strong reasoning capabilities but high cost and limited explicit SOTA tiering [Nov][RAg].

These systems demonstrate that LLMs can assist ideation, but they typically rely on:

- document-level similarity,
- post-hoc novelty checks,
- or implicit SOTA grounding via retrieval alone.

### 3.2 Research gaps

As summarized in the FGGV evaluation document [FGGV Doc], common limitations are:

- lack of a **joint** treatment of (i) landscape construction, (ii) explicit gap matrices, and (iii) **facet-level** verification,
- limited control over how SOTA is defined and exposed to reviewers,
- partial or opaque evaluation protocols.

POST-Rec is designed explicitly to:

- make the SOTA definition configurable and inspectable, and
- integrate facet-level novelty and gap alignment in a reproducible pipeline.

## 4. Data Sources and SOTA Definition

### 4.1 Data sources

POST-Rec currently uses **OpenAlex** as its primary literature source [OA]. Retrieval is implemented via the OpenAlex REST API with:

- field, subfield, and topic filters,
- filters on paratext and open-access metadata,
- rate limiting and circuit-breaking strategies [Retrieval Resilience].

All documents are normalized into a common schema with, at minimum:

- title,
- abstract (when available),
- DOI,
- publication year,
- citation counts,
- venue/journal information (when available).

### 4.2 SOTA subset construction

For each run, POST-Rec constructs a **SOTA subset** of retrieved papers. The exact thresholds are configurable in `apps/api/shared/settings.py`, but conceptually SOTA is defined by:

- **Recency**: papers within the last \(Y\) years (default \(Y = 3\); `sota_recent_years`) [Settings].
- **Citation strength**: a minimum citation threshold for foundation vs recent papers (e.g., `sota_seminal_citation_threshold`) to distinguish classic, highly cited works from recent but less-cited SOTA [Settings].
- **Domain alignment**: filters based on field/subfield/topic relevance to the user’s research area and seed topics, using OpenAlex concepts [Retrieval Resilience].

From the normalized corpus:

1. A **foundation tier** selects highly cited, possibly older papers.
2. A **recent SOTA tier** selects recent papers passing recency and alignment thresholds.
3. A **hybrid retrieval layer** combines BM25, dense embeddings, and pgvector search to rank candidates, enforcing a quota of SOTA-tier papers in the final context [Hybrid Retrieval].

The **SOTA set** in POST-Rec therefore consists of those papers:

- that belong to the SOTA tier(s) given the configuration, and
- that survive subsequent relevance and novelty filters.

This definition is explicit and can be reconstructed from:

- environment settings (e.g., `sota_recent_years`, citation thresholds),
- retrieval logs,
- stored source document records.

## 5. System Architecture and Modes

### 5.1 High-level pipeline

For each user run, POST-Rec executes:

1. **Expectation parsing**  
   - Inputs: seed topics, research area, expected output, depth, constraints.  
   - Output: normalized expectation context used for retrieval and prompting.

2. **Hybrid retrieval and relevance filtering**  
   - Queries OpenAlex with lexical and concept filters.  
   - Applies hybrid BM25 + dense vector scoring and lexical overlap thresholds.  
   - Enforces SOTA vs foundation quotas.

3. **Landscape and gap analysis (SOTA pipeline)**  
   - Clusters and summarizes the literature landscape.  
   - Identifies common problem–method–data–evaluation patterns.  
   - Constructs a **gap matrix** that highlights under-served combinations.

4. **Idea proposal generation**  
   - LLM generates candidate ideas conditioned on the gap matrix and selected papers.  
   - Each idea is structured with fields such as `title`, `abstract`, `why_relevant`, and SOTA anchors.

5. **Verification and scoring**  
   - Checks for basic consistency (e.g., no invented DOIs when possible).  
   - Computes novelty and alignment scores from retrieved documents.  
   - Aggregates into a final ranking score.

### 5.2 Run modes

The main modes are:

- **Quick**: single-pass generation with streamlined novelty checks.
- **SOTA-grounded (SOTA)**: full landscape → gap matrix → critic pipeline.
- **Exploratory**: emphasizes broader novelty, potentially at reduced precision.
- **FGGV**: SOTA pipeline plus facet-level verification and diversity selection.
- **Auto**: always-on blind A/B assignment between SOTA and FGGV for evaluation [FGGV Doc].

Modes differ primarily in how steps 3–5 are configured and which verification components are activated.

## 6. SOTA-Grounded Pipeline in Detail

This section describes the SOTA mode in more detail, as it forms the baseline that FGGV extends.

### 6.1 Landscape construction

Using the SOTA subset and foundation tier:

- documents are embedded and grouped into thematic clusters,
- for each cluster, the system summarizes:
  - main problems,
  - key methods,
  - typical datasets and evaluation protocols,
  - notable limitations and open questions.

The result is a coarse-grained map of the literature around the user’s topics.

### 6.2 Gap matrix

From cluster summaries and SOTA anchors, POST-Rec constructs a **gap matrix**:

- rows correspond to problems or sub-problems,
- columns correspond to method families, data regimes, or evaluation setups,
- entries capture whether a given combination is:
  - well-covered,
  - partially explored,
  - sparsely or not covered.

This matrix is used to:

- propose ideas that intentionally target under-served combinations, and
- encode SOTA grounding by linking each gap back to concrete papers.

### 6.3 Idea generation and critic

The SOTA pipeline then:

1. Samples candidate gaps from the matrix, biased towards under-served cells.  
2. Prompts the LLM to propose structured ideas that:
   - explicitly identify the targeted gap,
   - cite SOTA anchors from the retrieved set,
   - describe why the proposal is feasible and non-trivial.
3. Applies an internal critic:
   - rejects ideas that cannot be grounded in retrieved evidence,
   - downranks ideas that are too close to existing works.

The SOTA score used for ranking includes:

- relevance to the user expectation,
- SOTA alignment strength,
- basic document-level novelty.

## 7. FGGV: Facet-Grounded Gap Verification

FGGV is described in detail in the dedicated evaluation document [FGGV Doc]. Here we summarize how it relates to the SOTA pipeline.

### 7.1 Literature facet map (LFM)

- Each paper in the selected corpus is decomposed into facets such as `problem`, `method`, `data`, and `evaluation`.  
- These facet statements are embedded and stored in a **literature facet map** (LFM) with per-facet saturation scores (how crowded each facet is).

### 7.2 Gap–facet alignment (GFA)

- Each generated idea outputs `facet_deltas` (what changes relative to SOTA) and `aligned_gaps` (which cells of the gap matrix it claims to address).  
- GFA scores measure how well these declared deltas align with the pre-computed gap matrix, penalizing ideas that target already well-covered areas.

### 7.3 Contrastive facet novelty (CFN)

- For each facet, FGGV computes a **Facet Novelty Index (FNI)** = 1 − max similarity to same-facet statements in the LFM.  
- Weighting differences across facets reflect that novelty in method or problem is often more important than novelty in evaluation or data [FGGV Doc].

### 7.4 Facet diversity selection (FDS)

- After verification, candidate ideas are re-ranked with a Maximal Marginal Relevance (MMR)-style objective on facet tokens.  
- This encourages a final list with diverse facet combinations while maintaining high FGGV scores.

### 7.5 FGGV composite score

The FGGV score aggregates:

- base SOTA grounding,
- facet novelty (FNI),
- gap–facet alignment (GFA),
- document-level novelty,
- and penalties for “false novel” ideas where facets appear already saturated.

Implementation specifics (weights, thresholds, and ablation variants) are documented in [FGGV Doc] and the retrieval/verification modules in the POST-Rec codebase.

## 8. Evaluation and A/B Design

### 8.1 Offline evaluation

Offline evaluation focuses on:

- discriminating between **good** vs **weak** proposals on curated topics,
- comparing FGGV vs baselines B1–B3 and SOTA mode [Analysis Spec][FGGV Doc].

Metrics include:

- expert alignment scores,
- novelty proxy metrics,
- ranking metrics such as NDCG@K, MAP, and approval rate.

### 8.2 Online blind A/B (Auto mode)

The **Auto** mode in POST-Rec:

- uses a stable hashing scheme to assign each user deterministically to:
  - **control**: SOTA pipeline, or
  - **treatment**: FGGV-augmented pipeline;
- hides method labels and FGGV-specific scores for blind evaluation;
- records metrics such as:
  - expectation alignment score (EAS),
  - originality score,
  - approval/would-use rates.

An experiment dashboard aggregates these metrics by variant, enabling:

- continuous monitoring of FGGV vs SOTA behavior,
- export of anonymized data for more detailed analysis [Analysis Spec].

## 9. Discussion

### 9.1 Interpretability and transparency

Key design choices for reviewer transparency include:

- explicit SOTA definition based on recentness, citations, and domain filters, with configuration stored in settings,
- structured outputs that link each idea back to concrete evidence papers,
- detailed internal scores (e.g., FGGV components) stored alongside recommendations.

### 9.2 Limitations

Current limitations include:

- reliance on OpenAlex coverage and metadata quality,
- imperfect facet extraction and novelty estimation (subject to LLM biases),
- absence of direct head-to-head comparison with all existing ideation systems (e.g., Scideator, Idea Novelty Checker) on standardized benchmarks.

These limitations are partially mitigated by:

- expert studies on curated topics,
- ablation experiments on FGGV components,
- ongoing analysis of false-novel cases,
- the systematic literature review in [SLR], which maps POST-Rec SOTA/FGGV claims to 2023–2026 prior art.

A dedicated **systematic literature review** (`docs/systematic-literature-review.md`) evaluates whether POST-Rec’s operational SOTA definition and FGGV method align with recent ideation systems (Si et al., ResearchAgent, NOVA, Chain of Ideas, Scideator, Idea Novelty Checker, SciMON) and documents safe vs unsupported claims for reviewers.

## 10. Conclusion and Future Work

POST-Rec provides a reproducible, SOTA-grounded pipeline for research ideation, augmented with FGGV for facet-level gap verification and diversity. The system’s design emphasizes transparency: SOTA definition, retrieval configuration, verification steps, and evaluation methods are all documented and inspectable.

Future directions include:

- broader domain coverage beyond the initial focus areas,
- deeper integration with citation graphs and structured knowledge bases,
- more extensive human studies and cross-system comparisons,
- support for additional experimental pipelines beyond SOTA vs FGGV while reusing the same analysis framework.

## References

- [OA] Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully open index of scholarly works, authors, venues, and institutions. *arXiv preprint arXiv:2205.01833*.
- [FGGV Doc] *FGGV: Facet-Grounded Gap Verification*. `docs/fggv-evaluation.md` in the POST-Rec repository.
- [Retrieval Resilience] *Retrieval API Resilience*. `docs/retrieval-resilience.md` in the POST-Rec repository.
- [Analysis Spec] *POST-Rec Analysis Specification*. `docs/analysis-spec.md` in the POST-Rec repository.
- [Settings] *Application Settings*. `apps/api/shared/settings.py` in the POST-Rec repository (SOTA and retrieval-related parameters).
- [Hybrid Retrieval] Zuccon, G., Koopman, B., Deacon, A., et al. (2015). Integrating and evaluating neural and lexical retrieval models for health search. *Information Processing & Management*, 51(4), 475–488.
- [Si25] Si, X., et al. (2025). LLM-based Research Ideation Agent: Structuring the Literature for Novel Directions. *Proceedings of the International Conference on Learning Representations (ICLR)*.
- [Sci] Scideator project documentation, accessed 2026-06.
- [INC] Idea Novelty Checker project documentation, accessed 2026-06.
- [Nov] NOVA: Iterative planning for knowledge expansion. *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing*.
- [SLR] *Systematic Literature Review: SOTA Grounding and FGGV Positioning*. `docs/systematic-literature-review.md` in the POST-Rec repository.

