# Literature-Grounded Research Ideation with SOTA Pipelines and Facet-Grounded Gap Verification

> **Canonical version:** [`elsarticle/post-rec-ideation.tex`](elsarticle/post-rec-ideation.tex) (Elsevier elsarticle template, compile with `make` in `elsarticle/`)  
> This Markdown file is a readable draft; the LaTeX article is the submission-ready source.

**Paulo Roberto de Souza**  
Federal University of Bahia, Institute of Computing  
paulo.prsdesouza@ufba.br

**Frederico Araújo Durão**  
Federal University of Bahia, Institute of Computing  
fdurao@ufba.br

---

## Abstract

Researchers face a growing **literature overload** problem: the volume of scholarly work exceeds what any individual can survey before proposing new directions. Large language models (LLMs) can draft ideas quickly, but many outputs are weakly grounded in evidence, poorly aligned with the state of the art (SOTA), or difficult for reviewers to audit. This paper presents **POST-Rec** (Paper-Oriented Scientific Topic Recommender), a reproducible ideation system that combines hybrid bibliographic retrieval, an explicit SOTA subset definition, a multi-stage landscape → gap matrix → proposal pipeline, and an experimental extension called **Facet-Grounded Gap Verification (FGGV)** for facet-level novelty and gap alignment. Worked examples use a computer-science scenario (RAG-based research ideation). The deployed system evaluates methods **online** through a blind A/B study (SOTA vs FGGV) with volunteer feedback; offline harnesses support development regression only.

**Keywords:** Recommender Systems, Research Ideation, State of the Art, Retrieval-Augmented Generation, Facet Novelty Verification

---

## 1. Introduction

The exponential growth of scholarly publishing has increased literature overload in academic workflows. Researchers must decide which papers matter, which gaps remain open, and which proposals are genuinely novel—often under time pressure. Recent LLM-based ideation agents show promise, but they typically rely on document-level similarity, post-hoc novelty checks, or implicit SOTA grounding via retrieval alone.

This paper aims to investigate, model, and quantify literature-grounded research ideation through POST-Rec, which treats research proposal generation as a recommender problem over evidence-backed items:

1. retrieve and normalize articles from open catalogs,
2. construct an explicit **SOTA subset** per topic,
3. generate ideas through a multi-stage pipeline with inspectable artifacts,
4. verify novelty and SOTA alignment at document and facet levels,
5. learn from user feedback through an Expectation Alignment Score (EAS).

### 1.1 Main contributions

The main contributions of this work are:

- **The SOTA-grounded ideation pipeline**, which materializes landscape summaries and a gap matrix before proposal generation, making gap-driven ideation reproducible and auditable;
- **The hybrid retrieval and relevance model**, which combines dual-pass OpenAlex fetching, deterministic lexical relevance, BM25 + dense + pgvector ranking, and configurable SOTA tier quotas;
- **Facet-Grounded Gap Verification (FGGV)**, an extension that adds literature facet maps, gap–facet alignment, contrastive facet novelty, and diversity-aware selection;
- **The evaluation framework**, centered on **online** blind A/B between SOTA and FGGV with volunteer EAS/originality/approval metrics; offline harnesses for development regression; extended expert protocol planned.

This paper is structured as follows: Section 2 presents background. Section 3 discusses related work. Section 4 introduces the proposed system. Section 5 presents the evaluation design. Section 6 concludes and outlines future work.

---

## 2. Background

### 2.1 Recommender systems for scholarly content

Recommender systems filter large item collections to surface content aligned with user preferences. In scholarly settings, **items** are papers or research ideas, and **preferences** are expressed through seed topics, research area, depth, and constraints. Hybrid approaches that combine lexical signals, citation metadata, and dense embeddings are common when catalogs are large and metadata is noisy.

### 2.2 Literature-grounded ideation

Retrieval-augmented generation (RAG) grounds LLM outputs in retrieved documents. Recent ideation systems (e.g., Si et al., ResearchAgent, NOVA, SciMON, Scideator, Idea Novelty Checker) demonstrate that retrieval plus structured prompting improves relevance. However, few systems jointly expose (i) an explicit SOTA definition, (ii) a gap matrix artifact, and (iii) facet-level verification in one pipeline—gaps that POST-Rec targets directly.

### 2.3 State of the art as a configurable tier

In POST-Rec, “SOTA” is not a single community benchmark. It is a **proxy tier** built from recency, citations, and domain alignment—consistent with how 2023–2026 ideation systems operationalize “current work,” but made explicit and inspectable in settings and logs.

---

## 3. Related Work

| Approach | Retrieval | Gap structure | Novelty unit | Limitation |
|----------|-----------|---------------|--------------|------------|
| Si et al. (ICLR 2025) | Semantic Scholar API | Implicit in abstracts | Human-rated originality | No facet map or gap matrix |
| ResearchAgent | Citation graph | Agent review loops | Multi-agent debate | High cost; weak SOTA tiering |
| NOVA | Planned embedding search | Iterative broadening | Planning steps | Limited explicit SOTA exposure |
| Scideator | Paper pool facets | UI recombination | Facet-level checks | Weak explicit gap alignment |
| Idea Novelty Checker | Retrieve → rerank | Post-hoc | Per-facet LLM comparison | Not gap-driven generation |
| **POST-Rec SOTA** | OpenAlex dual-pass + hybrid rank | **Landscape + gap matrix** | Document + verified signals | LLM-synthesized gaps |
| **POST-Rec FGGV** | Same as SOTA | Gap matrix + LFM | **Per-facet FNI + GFA** | Requires human study for superiority claims |

A full systematic review is available in `docs/systematic-literature-review.md`.

---

## 4. The Proposal: POST-Rec

This section describes POST-Rec following the methodology pattern used in our prior recommender-system research: overview, data features, notation, preprocessing, component metrics, composite scores, and algorithms.

### 4.1 Recommendation overview

POST-Rec generates research ideas from user expectations and open literature. The macro pipeline comprises five major steps:

1. **Expectation parsing** — normalize seed topics, research area, depth, mode, and constraints;
2. **Dual-pass retrieval** — fetch recent SOTA-tier and foundation-tier papers from OpenAlex;
3. **Relevance filtering & hybrid ranking** — score, embed, and re-rank candidates with tier quotas;
4. **SOTA pipeline generation** — landscape → gap matrix → proposals → critic (mode-dependent);
5. **Verification & ranking** — novelty checks, SOTA fit, optional FGGV, verified `final_score`.

Ideas are presented to the user in descending order of verified score. Progress events in the UI map directly to these stages.

### 4.2 Data sources and document features

POST-Rec queries **OpenAlex** as its primary catalog, with optional merging from arXiv, Semantic Scholar, and Crossref metadata. Each document is normalized to:

| Feature | Role |
|---------|------|
| `title`, `abstract` | Lexical relevance, embeddings, generation context |
| `doi`, `year` | Deduplication, recency tiering |
| `citation_count` | Foundation tier, citation boost in relevance |
| `venue`, field/subfield/topic | Domain alignment filters |
| `openalex_fwci` (optional) | Field-weighted citation boost |

Rate limiting and circuit-breaking strategies are documented in `docs/retrieval-resilience.md`.

### 4.3 Notation

| Symbol | Description |
|--------|-------------|
| \(Q\) | Query token set from seed topics ∪ research area ∪ learned topics |
| \(p\) | A retrieved paper |
| \(T_{\text{title}}(p)\), \(T_{\text{body}}(p)\) | Token sets from title and body (title ∥ abstract ∥ venue) |
| \(O(A, Q)\) | Token overlap ratio \(\|A \cap Q\| / \|Q\|\) |
| \(s_{\text{rel}}(p)\) | Deterministic paper relevance score |
| \(e_d\) | Embedding vector for document \(d\) |
| \(\mathcal{S}_{\text{SOTA}}\) | SOTA-tier paper subset for the run |
| \(\mathcal{S}_{\text{found}}\) | Foundation-tier (seminal) subset |
| \(G\) | Gap matrix from landscape analysis |
| \(\text{FNI}_f\) | Facet Novelty Index for facet \(f\) |
| \(\text{GFA}\) | Gap–facet alignment score |
| \(S_{\text{verified}}\) | Verified final ranking score |

**Users and expectations** are represented as:

- **Expectation** \(E = \langle T_{\text{seed}}, A, O, D, C \rangle\) where \(T_{\text{seed}}\) are seed topics, \(A\) is research area, \(O\) expected output, \(D\) depth, \(C\) constraints.
- **Expanded topics:** \(T^* = \text{unique}(T_{\text{seed}} \cup T_{\text{learned}} \cup T_{\text{techniques}})\).

**Papers** retained after filtering:

\[
\mathcal{P} = \{ p \mid s_{\text{rel}}(p) \geq \tau_{\text{rel}} \}
\]

with default \(\tau_{\text{rel}} = 0.22\).

### 4.4 Paper preprocessing and modeling

Retrieved papers pass through normalization and deduplication:

1. **Normalize** — unify DOI, title casing, year, and source identifiers;
2. **Deduplicate** — merge on DOI, title hash, or content hash;
3. **Tag** — extract abstract limitations and method hints where available;
4. **Filter** — discard papers below \(s_{\text{rel}}\) or matching avoided-topic penalties;
5. **Embed** — \(e_d = \text{Embed}(\text{title}_d \parallel \text{abstract}_d)\).

### 4.5 Paper relevance score

Lexical overlap is computed after stopword removal and token length \(> 2\):

\[
O(A, Q) = \frac{|A \cap Q|}{|Q|}
\]

The relevance score combines title and body overlap with capped citation boost and avoided-topic penalty:

\[
s_{\text{rel}}(p) = 0.55 \cdot O(T_{\text{title}}, Q) + 0.30 \cdot O(T_{\text{body}}, Q) + b_{\text{cite}} - p_{\text{avoid}}
\]

\[
b_{\text{cite}} = \min\left(\frac{\ln(1 + c)}{12},\ 0.15\right)
\]

\[
p_{\text{avoid}} = 0.35 \quad \text{if avoided-topic tokens overlap the paper body}
\]

If both title and body overlap are very low, the score is capped at \(0.18\) unless area overlap provides a rescue path.

### 4.6 SOTA tier construction

For each run, POST-Rec builds two tiers (defaults from `apps/api/shared/settings.py`):

| Tier | Rule (default) |
|------|----------------|
| **SOTA recent** | Publication year ≥ current year − 3 (`sota_recent_years`) |
| **Seminal / foundation** | Citations ≥ 50 (`sota_seminal_citation_threshold`) |

Dual-pass retrieval fetches each tier separately. Hybrid re-ranking (BM25 + dense cosine + pgvector) enforces a **SOTA quota** of 60% (`sota_tier_quota`) in the final context passed to generation.

### 4.7 Hybrid re-ranking

Let \(s_{\text{sparse}}\) be BM25 score and \(s_{\text{dense}}\) cosine similarity between \(e_d\) and the query embedding. The hybrid score blends sparse and dense signals with vector retrieval, then applies tier quotas so recent SOTA papers dominate the evidence set without excluding seminal anchors.

### 4.8 Landscape and gap matrix

Using \(\mathcal{S}_{\text{SOTA}} \cup \mathcal{S}_{\text{found}}\), the SOTA pipeline:

1. clusters thematic groups from embeddings;
2. summarizes problems, methods, datasets, and evaluation protocols per cluster;
3. builds gap matrix \(G\) where rows are sub-problems and columns are method/data/eval families;
4. marks cells as well-covered, partial, or underserved.

Proposals intentionally target underserved cells and must link SOTA anchor papers from the retrieved set.

### 4.9 Verified ranking score

Published ideas receive a verified score blending LLM dimension estimates with deterministic signals:

\[
S_{\text{verified}} = \sum_i w_i \cdot \text{dim}_i + w_{\text{sota}} \cdot \text{SOTA\_fit} + w_{\text{nov}} \cdot \text{novelty\_verified}
\]

Default SOTA-mode weights (sum to 1):

| Component | Weight |
|-----------|--------|
| relevance | 0.16 |
| novelty (LLM) | 0.10 |
| evidence | 0.12 |
| feasibility | 0.11 |
| trend | 0.07 |
| publication_potential | 0.07 |
| strategic_fit | 0.07 |
| sota_fit (verified) | 0.16 |
| novelty_verified | 0.14 |

### 4.10 FGGV extension

**Facet-Grounded Gap Verification** augments the SOTA pipeline with four components:

1. **Literature Facet Map (LFM)** — decompose each paper into `{problem, method, data, evaluation}` facets with saturation scores;
2. **Gap–Facet Alignment (GFA)** — measure overlap between idea `facet_deltas` / `aligned_gaps` and matrix \(G\);
3. **Contrastive Facet Novelty (CFN)** — Facet Novelty Index \(\text{FNI}_f = 1 - \max \text{sim}(\text{facet}_f, \text{LFM}_f)\);
4. **Facet Diversity Selection (FDS)** — MMR re-ranking on facet tokens for diverse top-\(k\) lists.

Composite score (FGGV v2):

\[
\text{FGGV} = 0.30 \cdot S_{\text{verified}} + 0.32 \cdot \text{FNI} + 0.23 \cdot \text{GFA} + 0.15 \cdot \text{document\_novelty}
\]

### 4.11 Algorithms

**Algorithm 1: Paper relevance filtering**

```
Input: papers P, query tokens Q, threshold τ_rel
Output: filtered set P'
1. For each paper p ∈ P:
2.   Compute O(T_title, Q), O(T_body, Q)
3.   Compute b_cite from citation_count
4.   Apply p_avoid if avoided topics overlap body
5.   s_rel(p) ← weighted sum − penalties; apply weak-overlap cap
6.   If s_rel(p) ≥ τ_rel: add p to P'
7. Return P'
```

**Algorithm 2: SOTA-grounded idea generation**

```
Input: expectation E, ranked papers P, mode m
Output: candidate ideas I
1. Build landscape summary from P
2. Construct gap matrix G
3. Sample underserved cells from G
4. Prompt LLM with E, P, G, and evidence-only rules
5. Run critic: reject ungrounded or near-duplicate ideas
6. If mode = fggv: run LFM, GFA, CFN, FDS
7. Compute S_verified (and FGGV if applicable)
8. Return ranked ideas I
```

**Algorithm 3: Expectation Alignment Score (feedback loop)**

```
Input: user ratings (usefulness, relevance, clarity, feasibility, trust, would_use)
Output: EAS ∈ [1, 5]
1. Map would_use ∈ {yes, maybe, no} → {5, 3, 1}
2. EAS ← 0.25·U + 0.20·R + 0.20·C + 0.15·F + 0.10·T + 0.10·W
3. Update learned_topics / avoided_topics for future Q
4. Return EAS
```

---

## 5. Experimental Evaluation

### 5.1 Online evaluation (primary)

The deployed system validates methods **online**: volunteers run POST-Rec in **Auto** mode, receive blind assignment to SOTA (control) or FGGV (treatment), rate ideas, and contribute Expectation Alignment Scores. The validation dashboard aggregates metrics by `experiment_variant`. Method labels and FGGV sub-scores are hidden during blind runs.

### 5.2 Offline harness (supplementary)

`scripts/run_offline_evaluation.py` replays golden topics for engineering regression (B1/B2/M and ablations). It does not replace volunteer judgments in the current evaluation design.

### 5.3 Extended expert protocol (planned)

Complementary blind expert originality study (RQ1–RQ4) planned to augment online findings when sample size permits.

---

## 6. Conclusion and Future Work

POST-Rec provides a reproducible, SOTA-grounded pipeline for research ideation, with FGGV as an experimental extension for facet-level gap verification. Following the methodology tradition of explicit notation, component metrics, composite scores, and algorithmic pseudocode, the system emphasizes **transparency**: SOTA tiers, retrieval configuration, verification steps, and evaluation hooks are documented and inspectable.

Future work includes broader domain coverage, deeper citation-graph integration, expanded human studies, and cross-system benchmarks against Scideator, Idea Novelty Checker, and ResearchAgent-style agents.

---

## References

1. Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully open index of scholarly works. *arXiv:2205.01833*.
2. Si, X., et al. (2025). Can LLMs Generate Novel Research Ideas? *ICLR 2025*.
3. Baek, J., et al. (2025). ResearchAgent. *NAACL 2025*.
4. Roy, S., et al. (2024). Scideator. *arXiv*.
5. Ramesh, K., et al. (2025). Idea Novelty Checker. *SDP @ ACL 2025*.
6. POST-Rec repository: `docs/how-it-works.md`, `docs/fggv-evaluation.md`, `docs/systematic-literature-review.md`.
