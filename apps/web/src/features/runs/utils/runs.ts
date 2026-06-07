import type { RecommendationRun } from "@/shared/types/api";

export function formatRunDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) {
    return "";
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

export function formatRunTopics(run: RecommendationRun, noTopicsLabel: string, maxLength = 80): string {
  const topics = (run.topics ?? []).join(", ") || noTopicsLabel;
  return topics.length > maxLength ? `${topics.slice(0, maxLength)}…` : topics;
}

const FAILED_STATUSES = new Set([
  "failed",
  "cancelled",
  "cost_limit_exceeded",
  "failed_schema_validation",
]);

export function isRunActive(status: string): boolean {
  return !["completed", ...FAILED_STATUSES].includes(status);
}

export type RunOutcome = "ready" | "in_progress" | "failed" | "incomplete";

export function getRunOutcome(run: RecommendationRun): RunOutcome {
  const recommendationCount = run.recommendation_count ?? 0;

  if (run.status === "completed") {
    return recommendationCount > 0 ? "ready" : "incomplete";
  }
  if (FAILED_STATUSES.has(run.status)) {
    return "failed";
  }
  return "in_progress";
}

export function groupRuns(runs: RecommendationRun[]) {
  const active: RecommendationRun[] = [];
  const ready: RecommendationRun[] = [];
  const other: RecommendationRun[] = [];

  for (const run of runs) {
    const outcome = getRunOutcome(run);
    if (outcome === "ready") {
      ready.push(run);
    } else if (outcome === "in_progress") {
      active.push(run);
    } else {
      other.push(run);
    }
  }

  return { active, completed: ready, other };
}

export function formatPercent(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDecimal(value: number, locale: string, digits = 2): string {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}
