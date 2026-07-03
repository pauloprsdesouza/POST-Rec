# POST-Rec Analysis Specification

This document defines metrics, data sources, and statistical methods used by the research report (`GET /api/v1/admin/evaluation/research-report`) and offline export scripts.

## Layers

| Layer | Purpose | Where computed |
|-------|---------|----------------|
| Human validation | EAS, approval, Likert dimensions | `human_metrics.py`, live DB |
| Ranking (IR) | NDCG, MAP, MRR, P@K, R@K | `ir_metrics.py`, `ranking_eval.py` |
| Inferential | Mann-Whitney, Welch t, Chi-square | `inferential.py` |
| Expert study | FNI vs expert ρ | `expert_labels.py` + `data/expert_labels.json` |

## Graded relevance (idea ranking)

```
relevance = (usefulness_score + originality_score) / 10
binary relevance = 1 if relevance >= 0.5 else 0
```

System rank: `RecommendationCandidate.final_score` descending.

## Primary endpoints

- **EAS** — weighted alignment score (see transparency page)
- **Approval rate** — `decision == approved`
- **NDCG@K** — K ∈ {3, 5}
- **Cronbach α** — across 6 Likert dimensions

## Hypothesis tests (A/B FGGV vs SOTA)

| Outcome | Test |
|---------|------|
| EAS, originality | Mann-Whitney U (n < 30) or Welch t-test |
| Approval, would-use | Chi-square 2×2 |

## Scripts

```bash
py scripts/export_analysis_dataset.py
py scripts/generate_research_report.py
```

## UI

- **Insights** (`/insights`) — operational KPIs and trends
- **Research report** (`/insights/research-report`) — full one-page stats for reviewers/co-authors
