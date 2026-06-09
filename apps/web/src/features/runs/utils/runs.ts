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

export function formatRelativeRunTime(iso: string | null | undefined, locale: string): string {
  if (!iso) {
    return "";
  }
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffSec = Math.round((then - now) / 1000);
  const absSec = Math.abs(diffSec);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });

  if (absSec < 60) {
    return rtf.format(Math.round(diffSec), "second");
  }
  if (absSec < 3600) {
    return rtf.format(Math.round(diffSec / 60), "minute");
  }
  if (absSec < 86400) {
    return rtf.format(Math.round(diffSec / 3600), "hour");
  }
  if (absSec < 604800) {
    return rtf.format(Math.round(diffSec / 86400), "day");
  }
  return formatRunDateTime(iso, locale);
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

const STATUS_PROGRESS_FLOORS: Record<string, number> = {
  queued: 2,
  started: 5,
  searching_papers: 10,
  normalizing_documents: 20,
  deduplicating_documents: 25,
  generating_embeddings: 40,
  ranking_candidates: 55,
  generating_recommendations: 75,
  validating_output: 88,
};

/** Ordered pipeline stages shown in the run progress UI. */
export const RUN_PIPELINE_STAGES = [
  "queued",
  "started",
  "searching_papers",
  "generating_embeddings",
  "ranking_candidates",
  "generating_recommendations",
  "validating_output",
] as const;

export type RunPipelineStage = (typeof RUN_PIPELINE_STAGES)[number];

const PIPELINE_STAGE_INDEX = Object.fromEntries(
  RUN_PIPELINE_STAGES.map((stage, index) => [stage, index]),
) as Record<RunPipelineStage, number>;

/** Map backend statuses to a pipeline step for the stepper (non-breaking alias support). */
export function resolvePipelineStage(status: string): RunPipelineStage | null {
  if (status === "normalizing_documents" || status === "deduplicating_documents") {
    return "searching_papers";
  }
  if (status in PIPELINE_STAGE_INDEX) {
    return status as RunPipelineStage;
  }
  return null;
}

export function getRunPipelineStageIndex(status: string): number {
  const stage = resolvePipelineStage(status);
  return stage ? PIPELINE_STAGE_INDEX[stage] : -1;
}

/** Format seconds elapsed since run start for live progress displays. */
export function formatRunElapsed(
  startedAt: string | null | undefined,
  locale: string,
  nowMs = Date.now(),
): string | null {
  if (!startedAt) {
    return null;
  }
  const elapsedSec = Math.max(0, Math.floor((nowMs - new Date(startedAt).getTime()) / 1000));
  if (elapsedSec < 60) {
    return new Intl.NumberFormat(locale, { style: "unit", unit: "second", unitDisplay: "narrow" }).format(elapsedSec);
  }
  const minutes = Math.floor(elapsedSec / 60);
  const seconds = elapsedSec % 60;
  const minuteLabel = new Intl.NumberFormat(locale, { style: "unit", unit: "minute", unitDisplay: "narrow" }).format(
    minutes,
  );
  if (seconds === 0) {
    return minuteLabel;
  }
  const secondLabel = new Intl.NumberFormat(locale, { style: "unit", unit: "second", unitDisplay: "narrow" }).format(
    seconds,
  );
  return `${minuteLabel} ${secondLabel}`;
}

/** Minimum visible progress for active runs so the bar never sits at 0% while work is underway. */
export function getRunDisplayProgress(run: Pick<RecommendationRun, "status" | "progress">): number {
  const progress = run.progress ?? 0;
  if (!isRunActive(run.status)) {
    return Math.min(Math.max(progress, 0), 100);
  }
  const floor = STATUS_PROGRESS_FLOORS[run.status] ?? 0;
  return Math.min(Math.max(progress, floor), 100);
}

export type RunOutcome = "ready" | "reviewed" | "in_progress" | "failed" | "incomplete";

export function getRunOutcome(run: RecommendationRun): RunOutcome {
  const recommendationCount = run.recommendation_count ?? 0;

  if (run.status === "completed") {
    if (recommendationCount === 0) {
      return "incomplete";
    }
    if (run.feedback_complete) {
      return "reviewed";
    }
    return "ready";
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
