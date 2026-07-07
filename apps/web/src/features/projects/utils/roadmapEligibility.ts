import type { WouldUse } from "@/features/runs/components/QuickFeedbackPanel";

export function wouldUseFromRating(rating: number): WouldUse {
  if (rating >= 4) return "yes";
  if (rating >= 3) return "maybe";
  return "no";
}

export function wouldUseFromFeedback(
  rating: number | null | undefined,
  decision?: string | null,
): WouldUse {
  if (decision === "approved") return "yes";
  if (decision === "save") return "maybe";
  if (decision === "rejected" || decision === "needs_revision") return "no";
  if (rating != null) return wouldUseFromRating(rating);
  return "maybe";
}

/** True when the user has positively committed to an idea (roadmap CTA). */
export function isRoadmapEligible(
  rating: number | null,
  wouldUse: WouldUse,
  decision?: string | null,
): boolean {
  if (wouldUse === "yes") return true;
  if (rating != null && rating >= 4) return true;
  if (decision === "approved") return true;
  return false;
}
