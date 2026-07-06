export type RecommendationSourceSection = "about" | "summary" | "method" | "evidence";

export interface RecommendationFieldMeta {
  labelKey: string;
  section: RecommendationSourceSection;
}

export const RECOMMENDATION_FIELD_META: Record<string, RecommendationFieldMeta> = {
  evidence_papers: { labelKey: "projects.source.fields.evidence", section: "evidence" },
  research_gap: { labelKey: "ideas.researchGap", section: "about" },
  research_question: { labelKey: "ideas.researchQuestion", section: "about" },
  expected_contribution: { labelKey: "ideas.contribution", section: "about" },
  hypothesis: { labelKey: "ideas.hypothesis", section: "summary" },
  related_work_summary: { labelKey: "ideas.relatedWork", section: "summary" },
  proposed_method: { labelKey: "ideas.proposedMethod", section: "method" },
  experimental_plan: { labelKey: "ideas.experimentalPlan", section: "method" },
  datasets: { labelKey: "ideas.datasets", section: "method" },
  evaluation_metrics: { labelKey: "ideas.metrics", section: "method" },
  risks: { labelKey: "ideas.risks", section: "method" },
  sota_summary: { labelKey: "ideas.sotaSummary", section: "method" },
  novelty_delta: { labelKey: "ideas.noveltyDelta", section: "summary" },
};

export function getRecommendationFieldMeta(field: string): RecommendationFieldMeta {
  return (
    RECOMMENDATION_FIELD_META[field] ?? {
      labelKey: field,
      section: "about",
    }
  );
}

export function recommendationFieldAnchorId(field: string): string {
  return `project-source-field-${field.replace(/[^a-z0-9_-]/gi, "-")}`;
}

export function recommendationSectionAnchorId(section: RecommendationSourceSection): string {
  return `project-source-${section}`;
}

export function getRecommendationFieldValue(
  recommendation: import("@/shared/types/api").Recommendation,
  field: string,
): string | string[] | null | undefined {
  switch (field) {
    case "evidence_papers":
      return null;
    case "datasets":
      return recommendation.datasets;
    case "evaluation_metrics":
      return recommendation.evaluation_metrics;
    case "risks":
      return recommendation.risks;
    default:
      return recommendation[field as keyof typeof recommendation] as string | null | undefined;
  }
}
