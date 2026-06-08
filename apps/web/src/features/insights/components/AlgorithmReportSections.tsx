import { useTranslation } from "react-i18next";

import type { ResearchReport } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";
import {
  CollapsibleBlock,
  DataTable,
  NarrativeCallout,
  ReportChapter,
  StatCard,
  StatGrid,
} from "@/features/insights/components/ReportPrimitives";
import { GroupedBarChart } from "@/features/insights/components/InsightCharts";

function algorithmLabel(t: (key: string) => string, algorithm: string): string {
  const key = `researchReport.algorithms.${algorithm}`;
  const label = t(key);
  return label === key ? algorithm.toUpperCase() : label;
}

export function AlgorithmComparisonChapter({
  report,
  locale,
  chapterNumber,
}: {
  report: ResearchReport;
  locale: string;
  chapterNumber: number;
}) {
  const { t } = useTranslation();
  const algorithms = report.algorithm_analysis?.algorithms ?? [];
  if (!algorithms.length) {
    return null;
  }

  const chartData = algorithms.map((item) => ({
    label: algorithmLabel(t, item.algorithm),
    eas: item.human_rates.average_eas,
    approval: item.human_rates.approval_rate * 100,
    ndcg: (item.ranking_metrics["ndcg@5"] ?? 0) * 100,
  }));

  const bestEas = [...algorithms].sort(
    (a, b) => b.human_rates.average_eas - a.human_rates.average_eas,
  )[0];
  const bestNdcg = [...algorithms].sort(
    (a, b) => (b.ranking_metrics["ndcg@5"] ?? 0) - (a.ranking_metrics["ndcg@5"] ?? 0),
  )[0];

  return (
    <ReportChapter
      number={chapterNumber}
      id="chapter-algorithms"
      title={t("researchReport.story.chapterAlgorithmsTitle")}
      lead={t("researchReport.story.chapterAlgorithmsLead")}
    >
      {bestEas && bestNdcg ? (
        <NarrativeCallout tone="neutral">
          <p className="mb-0">
            {t("researchReport.story.algorithmSummary", {
              bestEasAlgo: algorithmLabel(t, bestEas.algorithm),
              bestEas: formatDecimal(bestEas.human_rates.average_eas, locale),
              bestNdcgAlgo: algorithmLabel(t, bestNdcg.algorithm),
              bestNdcg: formatDecimal(bestNdcg.ranking_metrics["ndcg@5"] ?? 0, locale),
            })}
          </p>
        </NarrativeCallout>
      ) : null}

      <GroupedBarChart
        data={chartData}
        keys={["eas", "approval", "ndcg"]}
        labels={{
          eas: t("insights.avgEas"),
          approval: t("insights.approvalRate"),
          ndcg: "NDCG@5 ×100",
        }}
      />

      <DataTable
        columns={[
          { key: "algorithm", label: t("researchReport.algorithm") },
          { key: "n", label: "n", align: "right" },
          { key: "eas", label: t("insights.avgEas"), align: "right" },
          { key: "approval", label: t("insights.approvalRate"), align: "right" },
          { key: "would_use", label: t("insights.wouldUseRate"), align: "right" },
          { key: "ndcg5", label: "NDCG@5", align: "right" },
          { key: "map", label: "MAP", align: "right" },
          { key: "mrr", label: "MRR", align: "right" },
        ]}
        rows={algorithms.map((item) => ({
          algorithm: algorithmLabel(t, item.algorithm),
          n: item.human_rates.feedback_count,
          eas: formatDecimal(item.human_rates.average_eas, locale),
          approval: formatPercent(item.human_rates.approval_rate, locale),
          would_use: formatPercent(item.human_rates.would_use_rate, locale),
          ndcg5: formatDecimal(item.ranking_metrics["ndcg@5"] ?? 0, locale),
          map: formatDecimal(item.ranking_metrics.map ?? 0, locale),
          mrr: formatDecimal(item.ranking_metrics.mrr ?? 0, locale),
        }))}
      />

      <CollapsibleBlock title={t("researchReport.story.algorithmRatingDetails")}>
        <DataTable
          columns={[
            { key: "algorithm", label: t("researchReport.algorithm") },
            { key: "relevance", label: t("researchReport.dimensions.relevance"), align: "right" },
            { key: "originality", label: t("researchReport.dimensions.originality"), align: "right" },
            { key: "clarity", label: t("researchReport.dimensions.clarity"), align: "right" },
            { key: "feasibility", label: t("researchReport.dimensions.feasibility"), align: "right" },
            { key: "trust", label: t("researchReport.dimensions.trust"), align: "right" },
            { key: "usefulness", label: t("researchReport.dimensions.usefulness"), align: "right" },
          ]}
          rows={algorithms.map((item) => ({
            algorithm: algorithmLabel(t, item.algorithm),
            relevance: formatDecimal(item.human_rates.average_relevance ?? 0, locale),
            originality: formatDecimal(item.human_rates.average_originality ?? 0, locale),
            clarity: formatDecimal(item.human_rates.average_clarity ?? 0, locale),
            feasibility: formatDecimal(item.human_rates.average_feasibility ?? 0, locale),
            trust: formatDecimal(item.human_rates.average_trust ?? 0, locale),
            usefulness: formatDecimal(item.human_rates.average_usefulness ?? 0, locale),
          }))}
        />
      </CollapsibleBlock>

      <CollapsibleBlock title={t("researchReport.story.algorithmRankingDetails")}>
        <DataTable
          columns={[
            { key: "algorithm", label: t("researchReport.algorithm") },
            { key: "ndcg1", label: "NDCG@1", align: "right" },
            { key: "ndcg3", label: "NDCG@3", align: "right" },
            { key: "ndcg10", label: "NDCG@10", align: "right" },
            { key: "err5", label: "ERR@5", align: "right" },
            { key: "p5", label: "P@5", align: "right" },
            { key: "r5", label: "R@5", align: "right" },
            { key: "hit1", label: "Hit@1", align: "right" },
          ]}
          rows={algorithms.map((item) => ({
            algorithm: algorithmLabel(t, item.algorithm),
            ndcg1: formatDecimal(item.ranking_metrics["ndcg@1"] ?? 0, locale),
            ndcg3: formatDecimal(item.ranking_metrics["ndcg@3"] ?? 0, locale),
            ndcg10: formatDecimal(item.ranking_metrics["ndcg@10"] ?? 0, locale),
            err5: formatDecimal(item.ranking_metrics["err@5"] ?? 0, locale),
            p5: formatDecimal(item.ranking_metrics["precision@5"] ?? 0, locale),
            r5: formatDecimal(item.ranking_metrics["recall@5"] ?? 0, locale),
            hit1: formatDecimal(item.ranking_metrics["hit@1"] ?? 0, locale),
          }))}
        />
      </CollapsibleBlock>
    </ReportChapter>
  );
}

export function ObservabilityChapter({
  report,
  locale,
  chapterNumber,
}: {
  report: ResearchReport;
  locale: string;
  chapterNumber: number;
}) {
  const { t } = useTranslation();
  const overall = report.observability?.overall;
  const byAlgorithm = report.observability?.by_algorithm ?? {};
  if (!overall) {
    return null;
  }

  return (
    <ReportChapter
      number={chapterNumber}
      id="chapter-observability"
      title={t("researchReport.story.chapterObservabilityTitle")}
      lead={t("researchReport.story.chapterObservabilityLead")}
    >
      <StatGrid>
        <StatCard
          label={t("researchReport.observability.completionRate")}
          value={formatPercent(overall.completion_rate ?? 0, locale)}
        />
        <StatCard
          label={t("researchReport.observability.failureRate")}
          value={formatPercent(overall.failure_rate ?? 0, locale)}
        />
        <StatCard
          label={t("researchReport.observability.avgCost")}
          value={`$${formatDecimal(overall.avg_cost_per_run_usd ?? 0, locale)}`}
        />
        <StatCard
          label={t("researchReport.observability.feedbackCoverage")}
          value={formatPercent(overall.feedback_coverage_rate ?? 0, locale)}
        />
      </StatGrid>

      {Object.keys(byAlgorithm).length > 0 ? (
        <DataTable
          columns={[
            { key: "algorithm", label: t("researchReport.algorithm") },
            { key: "runs", label: t("researchReport.runs"), align: "right" },
            { key: "completion", label: t("insights.completionRate"), align: "right" },
            { key: "cost", label: t("researchReport.observability.avgCost"), align: "right" },
            { key: "duration", label: t("researchReport.observability.avgDuration"), align: "right" },
            { key: "coverage", label: t("researchReport.observability.feedbackCoverage"), align: "right" },
          ]}
          rows={Object.entries(byAlgorithm).map(([algorithm, metrics]) => ({
            algorithm: algorithmLabel(t, algorithm),
            runs: metrics.run_count ?? 0,
            completion: formatPercent(metrics.completion_rate ?? 0, locale),
            cost: `$${formatDecimal(metrics.avg_cost_per_run_usd ?? 0, locale)}`,
            duration:
              metrics.avg_duration_seconds != null
                ? `${Math.round(metrics.avg_duration_seconds)}s`
                : "—",
            coverage: formatPercent(metrics.feedback_coverage_rate ?? 0, locale),
          }))}
        />
      ) : null}

      {report.algorithm_analysis?.engagement_funnel?.length ? (
        <CollapsibleBlock title={t("researchReport.story.engagementFunnel")}>
          <DataTable
            columns={[
              { key: "stage", label: t("researchReport.observability.stage") },
              { key: "count", label: t("researchReport.observability.count"), align: "right" },
            ]}
            rows={report.algorithm_analysis.engagement_funnel.map((step) => ({
              stage: t(`researchReport.observability.stages.${step.stage}`, step.stage),
              count: step.count,
            }))}
          />
        </CollapsibleBlock>
      ) : null}
    </ReportChapter>
  );
}

export function LiteratureMetricsChapter({
  report,
  locale,
  chapterNumber,
}: {
  report: ResearchReport;
  locale: string;
  chapterNumber: number;
}) {
  const { t } = useTranslation();
  const suite = report.algorithm_analysis?.literature_suite;
  if (!suite) {
    return null;
  }

  return (
    <ReportChapter
      number={chapterNumber}
      id="chapter-literature"
      title={t("researchReport.story.chapterLiteratureTitle")}
      lead={t("researchReport.story.chapterLiteratureLead")}
    >
      <NarrativeCallout tone="neutral">
        <p className="mb-0">{t("researchReport.story.literatureNote")}</p>
      </NarrativeCallout>

      <StatGrid>
        <StatCard label="NDCG@5" value={formatDecimal(suite.overall["ndcg@5"] ?? 0, locale)} highlight />
        <StatCard label="MAP" value={formatDecimal(suite.overall.map ?? 0, locale)} />
        <StatCard label="MRR" value={formatDecimal(suite.overall.mrr ?? 0, locale)} />
        <StatCard label="ERR@5" value={formatDecimal(suite.overall["err@5"] ?? 0, locale)} />
      </StatGrid>

      <CollapsibleBlock title={t("researchReport.story.literatureByAlgorithm")}>
        <DataTable
          columns={[
            { key: "algorithm", label: t("researchReport.algorithm") },
            { key: "ndcg5", label: "NDCG@5", align: "right" },
            { key: "map", label: "MAP", align: "right" },
            { key: "mrr", label: "MRR", align: "right" },
            { key: "err5", label: "ERR@5", align: "right" },
            { key: "p5", label: "P@5", align: "right" },
            { key: "hit1", label: "Hit@1", align: "right" },
          ]}
          rows={Object.entries(suite.by_algorithm).map(([algorithm, metrics]) => ({
            algorithm: algorithmLabel(t, algorithm),
            ndcg5: formatDecimal(metrics["ndcg@5"] ?? 0, locale),
            map: formatDecimal(metrics.map ?? 0, locale),
            mrr: formatDecimal(metrics.mrr ?? 0, locale),
            err5: formatDecimal(metrics["err@5"] ?? 0, locale),
            p5: formatDecimal(metrics["precision@5"] ?? 0, locale),
            hit1: formatDecimal(metrics["hit@1"] ?? 0, locale),
          }))}
        />
      </CollapsibleBlock>

      <CollapsibleBlock title={t("researchReport.story.literatureReferences")}>
        <DataTable
          columns={[
            { key: "metric", label: t("researchReport.story.metric") },
            { key: "citation", label: t("researchReport.story.citation") },
            { key: "use", label: t("researchReport.story.useCase") },
          ]}
          rows={(suite.references ?? []).map((ref) => ({
            metric: ref.metric,
            citation: ref.citation,
            use: ref.use,
          }))}
        />
      </CollapsibleBlock>
    </ReportChapter>
  );
}

export function InsightAnalysisChapter({
  report,
  locale,
  chapterNumber,
}: {
  report: ResearchReport;
  locale: string;
  chapterNumber: number;
}) {
  const { t } = useTranslation();
  const insights = report.insight_analysis;
  if (!insights) {
    return null;
  }

  return (
    <ReportChapter
      number={chapterNumber}
      id="chapter-insights-deep"
      title={t("researchReport.story.chapterInsightsTitle")}
      lead={t("researchReport.story.chapterInsightsLead")}
    >
      <div className="research-report__insight-grid">
        <div>
          <h3 className="research-report__mini-heading">{t("researchReport.story.decisionMix")}</h3>
          <DataTable
            columns={[
              { key: "decision", label: t("researchReport.story.decision") },
              { key: "count", label: "n", align: "right" },
            ]}
            rows={Object.entries(insights.decision_distribution).map(([decision, count]) => ({
              decision,
              count,
            }))}
          />
        </div>
        <div>
          <h3 className="research-report__mini-heading">{t("researchReport.story.wouldUseMix")}</h3>
          <DataTable
            columns={[
              { key: "answer", label: t("researchReport.story.answer") },
              { key: "count", label: "n", align: "right" },
            ]}
            rows={Object.entries(insights.would_use_distribution).map(([answer, count]) => ({
              answer,
              count,
            }))}
          />
        </div>
      </div>

      {insights.survey_hit_at_1.count > 0 ? (
        <NarrativeCallout tone="neutral">
          <p className="mb-0">
            {t("researchReport.story.surveyHitStory", {
              rate: formatPercent(insights.survey_hit_at_1.hit_at_1 ?? 0, locale),
              count: insights.survey_hit_at_1.count,
            })}
          </p>
        </NarrativeCallout>
      ) : null}

      {insights.cost_vs_quality.length > 0 ? (
        <CollapsibleBlock title={t("researchReport.story.costQuality")}>
          <GroupedBarChart
            data={insights.cost_vs_quality.map((point) => ({
              label: algorithmLabel(t, point.algorithm),
              eas: point.average_eas,
              cost: point.avg_cost_per_run_usd * 100,
            }))}
            keys={["eas", "cost"]}
            labels={{
              eas: t("insights.avgEas"),
              cost: t("researchReport.story.costScaled"),
            }}
          />
          <DataTable
            columns={[
              { key: "algorithm", label: t("researchReport.algorithm") },
              { key: "eas", label: t("insights.avgEas"), align: "right" },
              { key: "cost", label: t("researchReport.observability.avgCost"), align: "right" },
              { key: "n", label: "n", align: "right" },
            ]}
            rows={insights.cost_vs_quality.map((point) => ({
              algorithm: algorithmLabel(t, point.algorithm),
              eas: formatDecimal(point.average_eas, locale),
              cost: `$${formatDecimal(point.avg_cost_per_run_usd, locale)}`,
              n: point.feedback_count,
            }))}
          />
        </CollapsibleBlock>
      ) : null}
    </ReportChapter>
  );
}
