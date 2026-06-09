# FGGV: Facet-Grounded Gap Verification

This document positions POST-Rec's proposed method against recent literature and defines an empirical validation protocol suitable for an A1 journal submission.

## 1. State of the art (what existing work already does)

| Work | Core idea | Novelty handling | Gap / SOTA grounding | Known limitation |
|------|-----------|------------------|----------------------|------------------|
| **Si et al. (ICLR 2025)** — LLM research ideation agent | RAG over papers → idea generation | Human-rated originality; no facet decomposition | Implicit via retrieval | Novelty–feasibility tradeoff; limited diversity |
| **Scideator** | Facet recombination from paper pool | Facet-level novelty checker | Recombines existing facets | Less explicit gap-matrix alignment |
| **Idea Novelty Checker** | Retrieve → rerank → facet LLM comparison | Expert-labeled ICL examples per facet | Post-hoc verification | Not integrated with gap-driven generation |
| **NOVA** | Iterative planning for knowledge expansion | Planning steps | Expands retrieval iteratively | Heavy pipeline; weak explicit SOTA tiering |
| **ResearchAgent** | Multi-agent citation graph reasoning | Agent debate | Citation graph | Cost/complexity; no calibrated ranking loop |

**Common gap:** Document-level similarity or post-hoc facet checks, without **joint** (i) structured gap identification, (ii) **per-facet contrastive verification** against a literature facet map, and (iii) **diversity-aware selection** in one reproducible pipeline.

## 2. Proposed method: FGGV

**Facet-Grounded Gap Verification (FGGV)** extends the POST-Rec SOTA pipeline with four novel components:

### 2.1 Literature Facet Map (LFM)

For each retrieved paper, extract facets `{problem, method, data, evaluation}` and build a corpus-level facet index with saturation scores.

### 2.2 Gap-Facet Alignment (GFA)

Proposals declare `facet_deltas` and `aligned_gaps`. GFA scores token/semantic overlap between facet deltas and the gap matrix from the landscape stage.

### 2.3 Contrastive Facet Novelty (CFN)

**Facet Novelty Index (FNI):** per-facet novelty = 1 − max similarity to same-facet statements in the LFM (embedding or token fallback). Weighted: method 0.35, problem 0.30, evaluation 0.20, data 0.15.

### 2.4 Facet Diversity Selection (FDS)

After verification, MMR on facet token sets selects diverse top-k recommendations (addresses Si et al. diversity limitation).

### 2.5 FGGV composite score

```
FGGV = 0.30·verified_base + 0.32·FNI + 0.23·GFA + 0.15·document_novelty
```

### 2.6 FGGV v2 enhancements (implemented)

| Enhancement | vs literature | Purpose |
|-------------|---------------|---------|
| **Saturation-aware FNI (SA-FNI)** | Beyond Scideator uniform facets | Boost under-served facets; penalize duplicates in crowded facets |
| **LLM facet critic** | Idea Novelty Checker–style | Per-facet novelty judgment with false-novel risk |
| **Per-facet false-novel guard** | — | Flag ≥2 low-novelty facets → `needs_refinement` |
| **Closest facet match attribution** | Interpretability | Paper title + similarity per facet in `scores._fggv` |
| **Underserved-facet prompting** | — | Generation targets sparse facets from LFM |
| **Ablation harness** | Paper table 5 variants | `m_fggv_no_gfa`, `m_fggv_no_cfn`, `m_fggv_no_saturation` |

Run mode: `fggv` in the API/UI. Method version tag: `fggv_v2`.

## 3. Baselines (implemented for comparison)

| ID | Method | POST-Rec mode / config |
|----|--------|------------------------|
| **B1** | Single-pass RAG + document novelty | `quick` |
| **B2** | SOTA pipeline (landscape → gaps → proposals) | `sota` |
| **B3** | RAG without verification (ablation) | `b3_rag_no_verify` (offline harness only) |
| **M** | FGGV (proposed) | `fggv` |
| **M−GFA** | Ablation | harness `m_fggv_no_gfa` |
| **M−CFN** | Ablation | harness `m_fggv_no_cfn` |
| **M−SAT** | Ablation | harness `m_fggv_no_saturation` |

Offline harness:

```bash
python scripts/run_offline_evaluation.py
python scripts/run_offline_evaluation.py --ablations --output reports/fggv_full.json
```

Expert study labels: `data/expert_labels_template.json` + `correlate_fni_with_expert_originality()`.

## 4. Empirical validation protocol (for human study)

### Research questions

- **RQ1:** Does FGGV improve expert-rated originality vs B1/B2?
- **RQ2:** Does facet-level verification reduce "false novel" ideas vs document-level novelty?
- **RQ3:** Does FDS improve intra-list diversity without hurting relevance?
- **RQ4:** Do FNI/GFA correlate with blind expert originality scores?

### Metrics

| Metric | Definition |
|--------|------------|
| **Expert originality** | Likert 1–7, blind, per idea (primary) |
| **Feasibility** | Likert 1–7 (secondary — expect tradeoff) |
| **Anchor validity** | % ideas with verifiable SOTA anchor in retrieved set |
| **False-novel rate** | % ideas experts label as "already done" |
| **List diversity** | Average pairwise facet Jaccard distance in top-k |
| **FNI–expert ρ** | Spearman correlation |

### Design

- **Within-subjects:** Same topics, all baselines, counterbalanced order.
- **Topics:** 8–12 areas from golden set + held-out domains.
- **Experts:** 15–30 PhD+ researchers (2+ per idea for ICC).
- **Blinding:** Strip method labels; show only idea text + evidence.
- **Analysis:** Mixed-effects models (method fixed, topic/participant random); Holm-corrected pairwise tests vs FGGV.

### Minimum ablations (paper table)

1. FGGV full  
2. −FDS (no diversity selection)  
3. −GFA (no gap alignment term)  
4. −CFN (document novelty only)  
5. B2 SOTA pipeline  

## 5. What you can run today

```bash
# Unit + evaluation tests
pytest tests/unit/test_fggv.py tests/evaluation/test_fggv_harness.py -q

# Offline discriminability report (good vs weak proposals on golden fixture)
python scripts/run_offline_evaluation.py --output reports/fggv_offline.json
```

Live runs: select **FGGV (Facet-Grounded)** mode when starting a run.

## 6. Live blind A/B (product evaluation)

When `EXPERIMENT_FGGV_VS_SOTA_ENABLED=true`, users who opt in (`avoid_real_user_experiments=false`) are randomly assigned **control (`sota`)** vs **treatment (`fggv`)** with sticky bucketing. The UI hides mode labels, FGGV-specific scores, and run cost.

| Setting | Default | Purpose |
|---------|---------|---------|
| `EXPERIMENT_FGGV_VS_SOTA_ENABLED` | `false` | Master switch |
| `EXPERIMENT_FGGV_VS_SOTA_ID` | `fggv_vs_sota_v1` | Study identifier stored on runs |
| `EXPERIMENT_TREATMENT_FRACTION` | `0.5` | Share assigned to FGGV |

**Enable for a pilot:**

```bash
EXPERIMENT_FGGV_VS_SOTA_ENABLED=true
```

**Analysis:** `GET /api/v1/validation/dashboard` includes an `experiment` section with EAS/originality/approval by variant. Admin export: `python scripts/export_anonymized_validation_data.py`.

**Migration:** `alembic upgrade head` (revision `008_experiment_assignment`).

## 7. Claim guidance for submission

**Defensible now (artifact + offline metrics):**

- Novel integrated method (LFM + GFA + CFN + FDS) with reproducible code  
- Baseline implementations and offline discriminability on golden topics  
- Transparent scoring stored in `scores._fggv`

**Requires human study before claiming "ahead of SOTA":**

- Expert originality significantly > B2 with adequate power  
- Lower false-novel rate vs document-level baselines  
- FNI correlates with expert judgments (ρ ≥ 0.4 target)

Do **not** claim superiority over Scideator/Idea Novelty Checker without direct comparison or expert study on matched topics.
