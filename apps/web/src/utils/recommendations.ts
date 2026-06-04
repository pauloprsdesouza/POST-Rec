import type { Recommendation } from "../types/api";

export function sortRecommendationsByScore(recommendations: Recommendation[]): Recommendation[] {
  return [...recommendations].sort(
    (left, right) => (right.final_score ?? -1) - (left.final_score ?? -1),
  );
}
