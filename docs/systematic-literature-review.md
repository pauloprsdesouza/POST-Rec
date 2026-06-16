# Systematic Literature Review: SOTA Grounding and FGGV Positioning in POST-Rec

**Review date:** June 2026  
**Time window:** January 2023 – June 2026 (≤ 3 years)  
**Scope:** LLM-based scientific ideation, literature-grounded novelty assessment, and gap-driven research proposal generation  
**System under review:** POST-Rec (`SOTA` pipeline and `FGGV` method)

---

## 1. Introduction

### 1.1 Motivation

POST-Rec claims two methodological contributions relevant to reviewers:

1. **SOTA-grounded ideation** — ideas are generated from an explicit recent-literature subset, a landscape summary, and a gap matrix.
2. **Facet-Grounded Gap Verification (FGGV)** — an extension that adds facet maps, gap–facet alignment, contrastive facet novelty, and diversity-aware selection.

This review asks:

- **RQ1:** Does POST-Rec’s SOTA pipeline reflect the state of the art in recent (≤ 3 years) literature on literature-grounded ideation?
- **RQ2:** What exactly counts as “SOTA” in POST-Rec, and is that definition consistent with how recent systems operationalize state of the art?
- **RQ3:** Does FGGV constitute a method **beyond** current SOTA systems, or is it primarily an integration of known components?
- **RQ4:** What evidence gaps remain before POST-Rec can claim methodological novelty or superiority?

### 1.2 Review design (PRISMA-inspired)

| Element | Choice |
|---------|--------|
| **Sources** | ACL Anthology, arXiv, OpenReview, Semantic Scholar / ADS metadata, project repositories |
| **Query themes** | “LLM research ideation”, “scientific idea generation RAG”, “novelty checker facet”, “literature gap”, “ResearchAgent”, “SciMON”, “Scideator”, “NOVA ideation”, “Chain of Ideas” |
| **Inclusion** | Peer-reviewed or widely cited preprints (≥ 2023); systems with retrieval + ideation and/or novelty verification; English |
| **Exclusion** | Pure chemistry/materials discovery without ideation pipeline; general RAG surveys without scientific ideation; works without retrievable methods description |
| **Synthesis** | Thematic coding on: retrieval strategy, SOTA operationalization, gap modeling, novelty unit (document vs facet), iteration, evaluation protocol |
| **Validation** | Cross-check against POST-Rec implementation (`apps/api/features/recommendations/pipeline.py`, `packages/postrec_core/retrieval/`, `packages/postrec_core/facets/`) |

---

## 2. Included Corpus (n = 14 primary works)

| ID | Work | Venue / year | Core contribution |
|----|------|--------------|-------------------|
| P1 | Wang et al. — **SciMON** | ACL 2024 | Inspiration retrieval + iterative contrastive novelty optimization |
| P2 | Si et al. — **Can LLMs Generate Novel Research Ideas?** | ICLR 2025 | Large-scale human study; RAG agent over Semantic Scholar |
| P3 | Si et al. — **Ideation–Execution Gap** | ICLR 2026 | Execution study; LLM ideas lose novelty advantage after implementation |
| P4 | Baek et al. — **ResearchAgent** | NAACL 2025 | Citation graph + entity store; multi-agent iterative review |
| P5 | Hu et al. — **NOVA** | ACL Findings 2025 | Iterative planning + search for diversity and novelty |
| P6 | Li et al. — **Chain of Ideas (CoI)** | EMNLP Findings 2025 | Literature chains mirroring domain evolution; Idea Arena evaluation |
| P7 | Roy et al. — **Scideator** | arXiv 2024 | Human–LLM facet recombination + facet-based novelty verification |
| P8 | Ramesh et al. — **Idea Novelty Checker (INC)** | SDP @ ACL 2025 | Retrieve–rerank; facet-based LLM re-ranking for novelty **assessment** |
| P9 | Lu et al. — **The AI Scientist** | arXiv 2024 | End-to-end ideation → code → paper pipeline |
| P10 | Tian et al. — **MLRC-BENCH** | OpenReview 2025 | Benchmark: subjective novelty vs measurable ML performance |
| P11 | Zhang et al. — **Deep Ideation** | arXiv 2025 | Concept-network agents; compares SciMON, ResearchAgent, SciAgents |
| P12 | Anonymous — **HindSight** | arXiv 2026 | Time-split evaluation against **future** high-impact papers |
| P13 | LiveIdeaBench authors — **Divergent thinking evaluation** | PMC 2025 | Minimal-context ideation; surveys SciMON, ResearchAgent, Scideator |
| P14 | Survey — **LLMs for Scientific Idea Generation** | arXiv 2025 | Taxonomy: RAG, multi-agent, inference-time scaling, creativity frameworks |

**Foundational retrieval references (outside window, cited for mechanism only):** Lewis et al. (2020) RAG; Sun et al. (2023) RankGPT facet re-ranking.

---

## 3. Thematic Synthesis of Recent Literature

### 3.1 Retrieval and “SOTA” operationalization

Recent systems agree that ideation must be **literature-grounded**, but they define “current work” differently:

| System | How “relevant / SOTA” literature is selected |
|--------|-----------------------------------------------|
| **P2 Si et al.** | LLM issues Semantic Scholar API calls; top-*k* per action; LLM reranks by relevance, empirical focus, and “inspiring” score |
| **P4 ResearchAgent** | Citation graph from seed paper + entity-centric knowledge store |
| **P5 NOVA** | Planned searches over embedding index (2022–2024 AI papers); iterative broadening |
| **P6 CoI** | Anchor paper + forward/backward chain selection (temporal progression) |
| **P1 SciMON** | Retrieves “inspiration” papers for contrastive novelty loops |
| **P8 INC** | Keyword + snippet retrieval → embedding filter → facet LLM rerank |
| **POST-Rec SOTA** | OpenAlex dual-pass (`foundation` + `sota`); tier tags (`sota_recent`, `seminal`, `peripheral`); hybrid BM25 + dense + pgvector; 60% SOTA-tier quota |

**Finding F1 (SOTA definition):** In 2023–2026 literature, “SOTA” is almost never defined as a formal community benchmark. Instead, systems use **proxies**: recency, citation influence, retrieval relevance, or graph proximity. POST-Rec’s `sota_recent` tier (publication year ≥ current_year − 3, default) and `seminal` tier (citations ≥ 50) are **consistent with this proxy tradition** but more explicit and configurable than most baselines.

**Finding F2 (gap vs POST-Rec):** POST-Rec is **stronger than P2** on structured landscape/gap modeling, but **weaker than P4/P5/P6** on graph traversal, iterative search planning, and temporal literature chains.

### 3.2 Gap identification and structured ideation

| System | Explicit gap / landscape structure |
|--------|-----------------------------------|
| **P2** | Implicit in retrieved abstracts; no gap matrix |
| **P4** | Problem → method → experiment; reviewer feedback loops |
| **P5** | Seed ideas refined via planned retrieval; no matrix |
| **P6** | Chain structure encodes progression, not gap cells |
| **P1** | Contrastive comparison to prior inspirations |
| **P7 Scideator** | Facet recombination UI; gaps implicit in user selection |
| **POST-Rec** | **Explicit** `sota_landscape` JSON + `gap_matrix` JSON before proposal generation |

**Finding F3:** Among included works, **only POST-Rec** uses an explicit **landscape → gap matrix → proposal** sequence in a single reproducible pipeline. ResearchAgent and NOVA iterate structurally but do not materialize a gap matrix artifact. This supports POST-Rec’s claim of **transparent gap-driven ideation**, with the caveat that the gap matrix is **LLM-synthesized**, not extracted from a curated knowledge graph.

### 3.3 Novelty verification unit

| System | Novelty unit | When verified |
|--------|-------------|-------------|
| **P1 SciMON** | Document-level idea vs inspirations | During iterative generation |
| **P7 Scideator** | Facet-level (purpose, mechanism, evaluation) | Post-generation checker |
| **P8 INC** | Facet-level (purpose, mechanism, evaluation, application) | **Assessment only** (not generation) |
| **P4 ResearchAgent** | Multi-criteria reviewer scores | Iterative refinement |
| **P5 NOVA** | Embedding distance + tournament | During search iterations |
| **POST-Rec FGGV** | Facet-level FNI + document novelty + gap alignment | During ranking / critic |

**Finding F4:** Facet-based novelty is **established** in P7 and P8 (2024–2025). FGGV is **not the first** facet novelty system. Its distinction is **coupling facet verification to a pre-computed gap matrix and saturation-aware LFM inside the generation pipeline**, not facet decomposition alone.

### 3.4 Evaluation protocols (critical for claims)

| Work | Evaluation type | Key lesson |
|------|-----------------|------------|
| **P2** | 100+ expert blind reviews | LLM ideas rated **more novel** than human ideas at ideation stage |
| **P3** | 43 experts execute ideas (~100 h each) | LLM novelty advantage **collapses** after execution |
| **P10** | ML benchmark tasks | Subjective “novel” ideas ≠ performance gains |
| **P12 HindSight** | Time-split future paper overlap | Ideation quality should be validated against **later publications** |
| **P6 Idea Arena** | Pairwise tournaments | Aligns better with human preferences than single scalar scores |

**Finding F5:** Recent literature strongly warns against equating **perceived novelty** with **research value**. POST-Rec’s blind A/B (SOTA vs FGGV) addresses internal comparison but does **not yet** satisfy P3/P10/P12 standards for external validity.

---

## 4. RQ1–RQ2: Is POST-Rec SOTA “Really” SOTA-Grounded?

### 4.1 What POST-Rec implements (code-grounded)

| Layer | Implementation | Literature alignment |
|-------|----------------|---------------------|
| **Retrieval** | OpenAlex; dual-pass foundation/SOTA; field/subfield/topic filters; citation expansion | Aligns with P2, P8 (broad retrieve + rerank); lacks P4 citation-graph depth |
| **SOTA tiering** | `classify_paper_tier`: `sota_recent` if year ≥ now−3; `seminal` if citations ≥ 50 | Explicit proxy superior to opaque reranking in P2; coarser than venue-based SOTA lists |
| **Hybrid ranking** | BM25 + dense cosine + pgvector; tier quota 60% | Standard IR practice; comparable to P8 embedding stage |
| **Landscape** | LLM JSON: methods, datasets, metrics, open_problems | **Beyond** P2/P1 single-pass context; comparable intent to P6 chains but different structure |
| **Gap matrix** | LLM JSON: gaps with supporting paper_ids | **Distinctive** among 2023–2026 systems (Finding F3) |
| **Proposals** | Structured JSON with `sota_anchors`, `novelty_delta`, `closest_prior_work` | Stronger provenance than P5; similar spirit to P4 experiment design |
| **Critic / validator** | Citation verification, SOTA-recent anchor requirement, recency gap | Aligns with P8 motivation (grounded assessment) but lighter than INC expert ICL |

### 4.2 Verdict on SOTA grounding

| Criterion | Meets recent SOTA? | Evidence |
|-----------|-------------------|----------|
| Literature-grounded generation | **Yes** | Dual retrieval + hybrid rank + evidence-only prompts |
| Explicit recent-work subset | **Yes** | `sota_recent` tier with 3-year default matches review window |
| Structured SOTA understanding | **Partially** | Landscape + gap matrix exist; both are LLM-abstractive, not community-curated |
| Iterative deepening | **No** | Single pass per stage vs P4/P5 multi-iteration |
| Graph / chain awareness | **No** | No citation-graph agent (P4) or CoI chains (P6) |
| Execution-grounded validation | **No** | No P3-style execution study |

**Overall (RQ1):** POST-Rec’s SOTA pipeline is **a legitimate, documentable implementation of 2023–2026 literature-grounded ideation**, with **above-average transparency** on gap structure. It is **not** a superset of the field’s best retrieval strategies (graph, planning, chains) and should be described as **“SOTA-grounded RAG with explicit landscape and gap artifacts”** rather than “state-of-the-art system” in the competitive sense.

**Overall (RQ2):** In POST-Rec, **SOTA = operationally defined** as:

> Retrieved papers tagged `sota_recent` (≤ 3 years old) plus `seminal` foundation papers, filtered for domain relevance, quota-selected into the generation context, and referenced as `sota_anchors` in proposals.

This is **defensible for reviewers** if disclosed (as in `docs/how-it-works.md`). It is **not** the same as “methods that won benchmark X in year Y” or expert-consensus SOTA.

---

## 5. RQ3: Does FGGV Go Beyond SOTA?

### 5.1 FGGV components mapped to literature

| FGGV component | Closest prior art | Relationship |
|----------------|-------------------|--------------|
| **LFM** (problem/method/data/evaluation facet map) | P7 Scideator; P8 INC facets | Same facet families; POST-Rec adds **saturation scores** over corpus |
| **GFA** (gap–facet alignment) | No direct equivalent in included corpus | **Novel integration**: links proposal `facet_deltas` + `aligned_gaps` to gap matrix |
| **CFN** (contrastive facet novelty index) | P1 SciMON contrastive loop; P8 facet comparison | CFN is **embedding/token contrastive per facet**, not iterative rewrite |
| **SA-FNI** (saturation-aware weights) | P5 NOVA diversity; P1 novelty pressure | Under-served facet boosting is **incremental** but not seen elsewhere as explicit formula |
| **FDS** (MMR facet diversity) | P5 NOVA; P1 diversity via iteration | Standard MMR on facet tokens; **necessary but not novel alone** |
| **LLM facet critic** | P8 INC expert ICL; P4 ReviewingAgents | POST-Rec critic lacks INC’s expert-labeled ICL examples |
| **Composite FGGV score** | P1 iterative stopping; P4 multi-metric review | Explicit weighted composite stored in `scores._fggv` |

### 5.2 Coverage matrix: FGGV vs recent SOTA capabilities

| Capability | P1 | P4 | P5 | P6 | P7 | P8 | POST-Rec SOTA | POST-Rec FGGV |
|------------|----|----|----|----|----|----|---------------|---------------|
| RAG retrieval | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Explicit gap structure | — | — | — | — | — | — | ✓ | ✓ |
| Facet decomposition | — | — | — | — | ✓ | ✓ | — | ✓ |
| Facet novelty scoring | ✓ | — | ✓ | ✓ | ✓ | ✓ | partial | ✓ |
| Gap–facet joint scoring | — | — | — | — | — | — | — | **✓** |
| Saturation-aware facets | — | — | — | — | — | — | — | **✓** |
| Diversity selection | — | — | ✓ | — | — | — | — | ✓ |
| Multi-agent iteration | — | ✓ | ✓ | — | partial | — | — | — |
| Human-in-the-loop facets | — | — | — | — | **✓** | — | — | — |
| Expert ICL novelty judge | — | — | — | — | — | **✓** | — | partial |

### 5.3 Verdict on FGGV novelty

**FGGV is beyond POST-Rec SOTA** in a **clear, implementable** sense:

- It adds **LFM + GFA + CFN + FDS + composite ranking** on top of the same landscape/gap pipeline.
- The **distinctive claim** is **joint gap-grounded facet verification** (GFA + aligned generation), not facet novelty alone.

**FGGV is beyond the field’s recent SOTA** only as an **integrative contribution**:

| Claim | Supported? | Reason |
|-------|------------|--------|
| “First facet-based system” | **No** | P7, P8 precede it |
| “First gap-matrix ideation” | **Partially** | POST-Rec SOTA already has gap matrix; FGGV **extends** it |
| “First joint gap + facet verification pipeline” | **Plausibly yes** | No included work combines all three artifacts |
| “Demonstrated superior ideas” | **Not yet** | Requires P2-scale human study or P3 execution study |

**Recommended positioning for reviewers:**

> FGGV is a **structured extension** of literature-grounded ideation that unifies gap-matrix planning (POST-Rec SOTA) with facet-map contrastive verification (inspired by Scideator and Idea Novelty Checker), plus saturation-aware ranking and diversity selection. It proposes a **testable hypothesis**: joint gap–facet verification reduces false-novel proposals compared to document-level SOTA ranking alone.

---

## 6. Gap Analysis and Threats to Validity

### 6.1 Where POST-Rec SOTA lags recent literature

1. **No iterative retrieval planning** (P5 NOVA) — POST-Rec retrieves once per run (with prefetch/cache), then generates.
2. **No citation-graph or entity-store augmentation** (P4 ResearchAgent) — limits cross-domain analogy.
3. **No literature chain modeling** (P6 CoI) — may miss evolutionary context within a subfield.
4. **No SciMON-style iterative rewrite until novelty threshold** (P1) — novelty checked post-hoc.
5. **Evaluation** — internal A/B only; no execution study (P3), no future-impact metric (P12).

### 6.2 Where FGGV lags recent novelty literature

1. **No expert in-context learning examples** in facet critic (P8 INC reports ~13% agreement gain from ICL).
2. **No interactive facet recombination** (P7 Scideator user study: human-selected facets preferred).
3. **Facet extraction quality** depends on LLM/heuristics — same vulnerability as P7/P8.
4. **False-novel detection** is proxy-based (`false_novel_facet_count`) — not validated against expert “already done” labels at scale.

### 6.3 Internal validity threats

| Threat | Mitigation in POST-Rec | Residual risk |
|--------|------------------------|---------------|
| LLM hallucinated gaps | `insufficient_evidence` flags; article validation | Gaps may still be plausible but wrong |
| Citation proxy ≠ influence | Citation counts for seminal tier | Misses fast-moving subfields |
| 3-year window too narrow | Configurable `sota_recent_years` | May exclude foundational theory |
| Auto mode SOTA vs FGGV A/B | Sticky bucketing; blind UI | Compares pipelines, not isolated components |

---

## 7. Implications for POST-Rec Documentation and Claims

### 7.1 Safe claims (evidence-backed)

- POST-Rec uses an **explicit, configurable operational definition of SOTA literature** (recent + seminal tiers, hybrid retrieval, anchor requirements).
- The SOTA pipeline implements a **documented landscape → gap matrix → proposal → critic** workflow rare in contemporaneous systems.
- FGGV adds **facet-level verification and gap alignment** not present in the SOTA-only path.
- Auto mode enables **continuous SOTA vs FGGV comparison** aligned with P2-style human feedback collection.

### 7.2 Claims to avoid until further studies

- “FGGV outperforms Scideator / Idea Novelty Checker / ResearchAgent” — **no direct benchmark**.
- “Ideas are more novel than human experts” — P2 found this at ideation, but P3 reversed after execution.
- “SOTA anchors guarantee methodological SOTA” — anchors are **retrieval-selected recent papers**, not community-validated best methods.

### 7.3 Recommended follow-up studies (mapped to literature)

| Priority | Study | Inspired by |
|----------|-------|-------------|
| 1 | Expert blind review: SOTA vs FGGV on matched topics | P2 |
| 2 | False-novel rate with expert “already done” labels | P8, P3 |
| 3 | Ablation: −GFA, −CFN, −FDS (already in harness) + human judges | FGGV doc |
| 4 | HindSight-style time-split evaluation on fixed cutoffs | P12 |
| 5 | Optional execution pilot (small N) | P3 |

---

## 8. Conclusion

### 8.1 Summary answers

| RQ | Answer |
|----|--------|
| **RQ1** | POST-Rec SOTA **does reflect** 2023–2026 literature on grounded ideation, with **stronger gap transparency** than most baselines but **weaker iteration/graph mechanisms** than ResearchAgent, NOVA, and Chain of Ideas. |
| **RQ2** | “SOTA” in POST-Rec means **recent + influential retrieved papers**, not field consensus. This is **standard for the genre** and must be stated clearly to reviewers. |
| **RQ3** | FGGV **extends** POST-Rec SOTA and **integrates** facet verification with gap alignment in a way **not shown as a unified pipeline** in the reviewed corpus. Individual mechanisms (facets, contrastive novelty, diversity) **have precedents**. |
| **RQ4** | Empirical superiority is **unproven**; P3 and P10 show ideation metrics alone are insufficient. |

### 8.2 Final assessment

POST-Rec is **methodologically serious and reviewer-auditable**: SOTA is implemented as more than a label—it is a retrieval tier, a landscape artifact, a gap matrix, and anchor constraints. FGGV is a **credible research contribution** if framed as **integrative facet-grounded gap verification**, not as a wholly unprecedented paradigm.

The system is **ready for transparent disclosure** (How it works, this SLR). It is **not yet ready** for strong superiority claims against 2024–2026 baselines without matched human or execution studies.

---

## References

1. Baek, J., Jauhar, S. K., Cucerzan, S., & Hwang, S. J. (2025). ResearchAgent: Iterative research idea generation over scientific literature with large language models. In *Proceedings of NAACL 2025* (pp. 1–30). https://aclanthology.org/2025.naacl-long.342/

2. Hu, X., Fu, H., Wang, J., Wang, Y., Li, Z., Xu, R., Lu, Y., Jin, Y., Pan, L., & Lan, Z. (2025). NOVA: An iterative planning framework for enhancing scientific innovation with large language models. In *Findings of ACL 2025* (pp. 21330–21359). https://aclanthology.org/2025.findings-acl.1099/

3. Li, L., et al. (2025). Chain of Ideas: Revolutionizing research via novel idea development with LLM agents. In *Findings of EMNLP 2025*. https://aclanthology.org/2025.findings-emnlp.477/

4. Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.

5. Lu, C., et al. (2024). The AI Scientist: Towards fully automated open-ended scientific discovery. *arXiv:2408.06292*.

6. Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully open index of scholarly works, authors, venues, and institutions. *arXiv:2205.01833*.

7. Qi, P., et al. (2023). Zero-shot hypothesis generation via large language models. *arXiv* (cited in P11).

8. Ramesh, K., et al. (2025). Literature-grounded novelty assessment of scientific ideas (Idea Novelty Checker). In *Proceedings of SDP @ ACL 2025*. https://aclanthology.org/2025.sdp-1.9/

9. Roy, S., et al. (2024). Human-LLM compound system for scientific ideation through facet recombination and novelty evaluation (Scideator). *arXiv:2409.14634*.

10. Si, C., Yang, D., & Hashimoto, T. (2025). Can LLMs generate novel research ideas? A large-scale human study with 100+ NLP researchers. In *ICLR 2025*. https://arxiv.org/abs/2409.04109

11. Si, C., Hashimoto, T., & Yang, D. (2026). The ideation–execution gap: Execution outcomes of LLM-generated versus human research ideas. *ICLR 2026*. https://openreview.net/forum?id=Fllp8l6Puy

12. Sun, W., et al. (2023). Is ChatGPT good at search? Investigating large language models as re-ranking agents. *EMNLP 2023* (RankGPT / facet re-ranking lineage).

13. Tian, M., et al. (2025). MLRC-BENCH: Can language agents solve machine learning research challenges? *OpenReview*.

14. Wang, Q., Downey, D., Ji, H., & Hope, T. (2024). SciMON: Scientific inspiration machines optimized for novelty. In *ACL 2024* (pp. 279–299). https://aclanthology.org/2024.acl-long.18/

15. Weng, Y., et al. (2024). CycleResearcher: Iterative research idea refinement with automated review feedback. *arXiv* (cited in P11).

16. Yang, C., et al. (2024). MOOSE-Chem: Training a molecular discovery LLM from knowledge graph mining. *arXiv* (cited in P11).

17. Zhang, et al. (2025). Deep ideation: Designing LLM agents to generate novel research ideas on scientific concept networks. *arXiv:2511.02238*.

18. Anonymous. (2026). HindSight: Evaluating LLM-generated research ideas via future impact. *arXiv:2603.15164*.

19. LiveIdeaBench authors. (2025). Evaluating LLMs’ divergent thinking capabilities for scientific idea generation with minimal context. *PMC*.

20. Survey authors. (2025). Large language models for scientific idea generation: A creativity-centered survey. *arXiv*.

21. POST-Rec project. (2026). FGGV: Facet-grounded gap verification. `docs/fggv-evaluation.md`.

22. POST-Rec project. (2026). System overview and methodology. `docs/how-it-works.md`.

23. Zuccon, G., Koopman, B., Deacon, A., et al. (2015). Integrating and evaluating neural and lexical retrieval models for information retrieval. *Information Processing & Management*, 51(4), 475–488.
