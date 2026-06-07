import type { RecommendationRun } from "@/shared/types/api";

export function isBlindRun(run: Pick<RecommendationRun, "presentation_profile"> | null | undefined): boolean {
  return run?.presentation_profile === "blind";
}
