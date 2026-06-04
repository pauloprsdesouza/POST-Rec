export const ACADEMIC_LEVELS = [
  "Undergraduate",
  "Masters",
  "PhD",
  "Professor",
  "Industry",
] as const;

export const EXPERIENCE_LEVELS = ["None", "Basic", "Intermediate", "Advanced"] as const;

export const CONSENT_VERSION = "v1.0";

export const DEFAULT_SEED_TOPICS = [
  "Generative AI in recommender systems",
  "RAG for explainable recommendations",
] as const;

export const RUN_STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  started: "Started",
  searching_papers: "Searching papers",
  embedding: "Embedding",
  generating: "Generating",
  generating_recommendations: "Generating recommendations",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};
