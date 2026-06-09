/** Display constants aligned with backend scoring (relevance_service, expectation_alignment). */

export const LITERATURE_SOURCES = [
  "OpenAlex",
  "arXiv",
  "Semantic Scholar",
  "Crossref",
] as const;

export const PIPELINE_STEPS = [
  "expectation",
  "retrieval",
  "relevance",
  "dedup",
  "embedding",
  "hybridRank",
  "sotaPipeline",
  "verification",
  "validation",
  "ranking",
] as const;

export const VERIFIED_RANKING_WEIGHTS: ReadonlyArray<{ key: string; weight: number }> = [
  { key: "relevance", weight: 0.16 },
  { key: "novelty (LLM)", weight: 0.10 },
  { key: "evidence", weight: 0.12 },
  { key: "feasibility", weight: 0.11 },
  { key: "trend", weight: 0.07 },
  { key: "publication_potential", weight: 0.07 },
  { key: "strategic_fit", weight: 0.07 },
  { key: "sota_fit (verified)", weight: 0.16 },
  { key: "novelty_verified", weight: 0.14 },
];

export const HYBRID_RETRIEVAL = {
  sparseWeight: 0.4,
  bm25Enabled: true,
  vectorRetrievalBlend: 0.25,
  sotaQuota: 0.6,
  dualPass: true,
} as const;

export const PAPER_RELEVANCE = {
  titleWeight: 0.55,
  bodyWeight: 0.3,
  citationBoostMax: 0.15,
  citationLogDivisor: 12,
  avoidPenalty: 0.35,
  minKeepScore: 0.22,
  weakOverlapCap: 0.18,
  titleWeakThreshold: 0.08,
  bodyWeakThreshold: 0.12,
} as const;

export const IDEA_SCORE_DIMENSIONS = [
  "relevance",
  "novelty",
  "evidence",
  "feasibility",
  "trend",
  "publication_potential",
  "strategic_fit",
] as const;

export const FINAL_RANKING_WEIGHTS: ReadonlyArray<{ key: (typeof IDEA_SCORE_DIMENSIONS)[number]; weight: number }> = [
  { key: "relevance", weight: 0.22 },
  { key: "novelty", weight: 0.18 },
  { key: "evidence", weight: 0.15 },
  { key: "feasibility", weight: 0.15 },
  { key: "trend", weight: 0.1 },
  { key: "publication_potential", weight: 0.1 },
  { key: "strategic_fit", weight: 0.1 },
];

export const EAS_WEIGHTS = [
  { key: "usefulness", weight: 0.25 },
  { key: "relevance", weight: 0.2 },
  { key: "clarity", weight: 0.2 },
  { key: "feasibility", weight: 0.15 },
  { key: "trust", weight: 0.1 },
  { key: "would_use", weight: 0.1 },
] as const;

export const WOULD_USE_SCORES = {
  yes: 5,
  maybe: 3,
  no: 1,
} as const;
