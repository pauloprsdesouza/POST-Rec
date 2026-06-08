import type { TFunction } from "i18next";

import type { ResearchReport } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";

export type NarrativeTone = "positive" | "neutral" | "caution";

export interface StoryHighlight {
  id: string;
  label: string;
  value: string;
  story: string;
  tone: NarrativeTone;
}

export interface ReportNarrative {
  headline: string;
  subheadline: string;
  highlights: StoryHighlight[];
  topDimension: { name: string; mean: number } | null;
  weakestDimension: { name: string; mean: number } | null;
  rankingVerdict: string;
  rankingTone: NarrativeTone;
  experimentVerdict: string | null;
  experimentTone: NarrativeTone | null;
}

function scoreTone(value: number, good: number, caution: number): NarrativeTone {
  if (value >= good) {
    return "positive";
  }
  if (value >= caution) {
    return "neutral";
  }
  return "caution";
}

function ndcgTone(value: number): NarrativeTone {
  return scoreTone(value, 0.7, 0.5);
}

export function buildReportNarrative(
  report: ResearchReport,
  t: TFunction,
  locale: string,
): ReportNarrative {
  const eas = Number(report.primary_outcomes.average_eas ?? 0);
  const approval = Number(report.primary_outcomes.approval_rate ?? 0);
  const wouldUse = Number(report.primary_outcomes.would_use_rate ?? 0);
  const ndcg5 = Number(report.ranking_metrics.overall["ndcg@5"] ?? 0);
  const feedback = report.sample.feedback;
  const runs = report.sample.runs;

  const sortedDimensions = [...report.descriptive_statistics].sort((a, b) => b.mean - a.mean);
  const topDimension = sortedDimensions[0]
    ? { name: sortedDimensions[0].dimension, mean: sortedDimensions[0].mean }
    : null;
  const weakestDimension =
    sortedDimensions.length > 1
      ? {
          name: sortedDimensions[sortedDimensions.length - 1].dimension,
          mean: sortedDimensions[sortedDimensions.length - 1].mean,
        }
      : null;

  const highlights: StoryHighlight[] = [];

  if (feedback > 0) {
    highlights.push({
      id: "eas",
      label: t("researchReport.story.highlights.easLabel"),
      value: formatDecimal(eas, locale),
      story: t(`researchReport.story.easVerdict.${scoreTone(eas, 4, 3)}`),
      tone: scoreTone(eas, 4, 3),
    });
    highlights.push({
      id: "approval",
      label: t("researchReport.story.highlights.approvalLabel"),
      value: formatPercent(approval, locale),
      story: t(`researchReport.story.approvalVerdict.${scoreTone(approval, 0.4, 0.25)}`),
      tone: scoreTone(approval, 0.4, 0.25),
    });
    highlights.push({
      id: "wouldUse",
      label: t("researchReport.story.highlights.wouldUseLabel"),
      value: formatPercent(wouldUse, locale),
      story: t(`researchReport.story.wouldUseVerdict.${scoreTone(wouldUse, 0.25, 0.15)}`),
      tone: scoreTone(wouldUse, 0.25, 0.15),
    });
  }

  if ((report.ranking_metrics.overall.run_count ?? 0) > 0) {
    highlights.push({
      id: "ranking",
      label: t("researchReport.story.highlights.rankingLabel"),
      value: formatDecimal(ndcg5, locale),
      story: t(`researchReport.story.rankingVerdict.${ndcgTone(ndcg5)}`),
      tone: ndcgTone(ndcg5),
    });
  }

  let experimentVerdict: string | null = null;
  let experimentTone: NarrativeTone | null = null;
  const tests = report.experiment_analysis?.hypothesis_tests;
  if (tests && "eas" in tests && tests.eas && "mann_whitney" in tests.eas) {
    const easTest = tests.eas.mann_whitney;
    const treatmentWins = easTest.group_b_mean > easTest.group_a_mean;
    if (easTest.significant_at_005) {
      experimentVerdict = treatmentWins
        ? t("researchReport.story.experimentSignificantTreatment")
        : t("researchReport.story.experimentSignificantControl");
      experimentTone = treatmentWins ? "positive" : "caution";
    } else {
      experimentVerdict = t("researchReport.story.experimentNotSignificant");
      experimentTone = "neutral";
    }
  }

  const headline =
    feedback > 0
      ? t("researchReport.story.headlineWithData", { feedback, runs })
      : t("researchReport.story.headlineEmpty");

  const subheadline =
    feedback > 0
      ? t("researchReport.story.subheadlineWithData")
      : t("researchReport.story.subheadlineEmpty");

  return {
    headline,
    subheadline,
    highlights,
    topDimension,
    weakestDimension,
    rankingVerdict: t(`researchReport.story.rankingVerdict.${ndcgTone(ndcg5)}`),
    rankingTone: ndcgTone(ndcg5),
    experimentVerdict,
    experimentTone,
  };
}

export function formatDimensionName(t: TFunction, dimension: string): string {
  return t(`researchReport.dimensions.${dimension}`, dimension);
}
