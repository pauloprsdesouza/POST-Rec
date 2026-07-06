import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { GroupComparison, HypothesisTestResult, ResearchReport } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";
import {
  buildReportNarrative,
  formatDimensionName,
} from "@/features/insights/utils/reportNarrative";
import {
  CollapsibleBlock,
  DataTable,
  NarrativeCallout,
  ReportChapter,
  ReportTableOfContents,
  SignificanceBadge,
  StatCard,
  StatGrid,
  StoryAtAGlance,
  StoryCard,
} from "@/features/insights/components/ReportPrimitives";
import {
  DistributionBarChart,
  GroupedBarChart,
  TrendLineChart,
} from "@/features/insights/components/InsightCharts";
import {
  AlgorithmComparisonChapter,
  InsightAnalysisChapter,
  LiteratureMetricsChapter,
  ObservabilityChapter,
} from "@/features/insights/components/AlgorithmReportSections";

function formatPValue(value: number | null | undefined): string {
  if (value == null) {
    return "—";
  }
  if (value < 0.001) {
    return "< 0.001";
  }
  return value.toFixed(4);
}

function isGroupComparison(value: GroupComparison | HypothesisTestResult): value is GroupComparison {
  return "mann_whitney" in value;
}

function HypothesisTestBlock({
  title,
  test,
  locale,
}: {
  title: string;
  test: GroupComparison | HypothesisTestResult;
  locale: string;
}) {
  const { t } = useTranslation();
  const primary: HypothesisTestResult = isGroupComparison(test)
    ? test.recommended_test === "welch_t_test"
      ? test.welch_t_test
      : test.mann_whitney
    : test;

  return (
    <div className="research-report__hypothesis">
      <div className="research-report__hypothesis-header">
        <h3 className="research-report__hypothesis-title">{title}</h3>
        <SignificanceBadge significant={primary.significant_at_005} />
      </div>
      <p className="research-report__hypothesis-interpretation">{primary.interpretation}</p>
      <CollapsibleBlock title={t("researchReport.story.testDetails")}>
        <DataTable
          columns={[
            { key: "metric", label: t("researchReport.story.metric") },
            { key: "value", label: t("researchReport.story.value"), align: "right" },
          ]}
          rows={[
            { metric: t("researchReport.story.testType"), value: primary.test_name },
            { metric: t("researchReport.story.statistic"), value: formatDecimal(primary.statistic, locale) },
            { metric: "p-value", value: formatPValue(primary.p_value) },
            {
              metric: primary.effect_size_name ?? t("researchReport.story.effectSize"),
              value: primary.effect_size != null ? formatDecimal(primary.effect_size, locale) : "—",
            },
            { metric: t("researchReport.story.groupAMean"), value: formatDecimal(primary.group_a_mean, locale) },
            { metric: t("researchReport.story.groupBMean"), value: formatDecimal(primary.group_b_mean, locale) },
            { metric: t("researchReport.story.groupAN"), value: primary.group_a_n },
            { metric: t("researchReport.story.groupBN"), value: primary.group_b_n },
          ]}
        />
      </CollapsibleBlock>
    </div>
  );
}

export function ResearchReportPage() {
  const { t, i18n } = useTranslation();
  const { accessToken } = useAuth();
  const locale = i18n.language;
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    adminService
      .getResearchReport(accessToken)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : t("researchReport.loadError")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

  const narrative = useMemo(
    () => (report ? buildReportNarrative(report, t, locale) : null),
    [report, t, locale],
  );

  const generatedLabel = useMemo(() => {
    if (!report?.generated_at) {
      return "";
    }
    return new Date(report.generated_at).toLocaleString(locale);
  }, [report, locale]);

  const modeChartData = useMemo(() => {
    if (!report?.mode_comparison?.length) {
      return [];
    }
    return report.mode_comparison.map((row) => ({
      label: String(row.mode),
      eas: Number(row.average_eas ?? 0),
      approval: Number(row.approval_rate ?? 0) * 100,
      would_use: Number(row.would_use_rate ?? 0) * 100,
    }));
  }, [report]);

  const experimentChartData = useMemo(() => {
    const variants = report?.experiment_analysis?.variants ?? [];
    return variants.map((row) => ({
      label: String(row.variant),
      eas: Number(row.average_eas ?? 0),
      originality: Number(row.average_originality ?? 0),
      approval: Number(row.approval_rate ?? 0) * 100,
    }));
  }, [report?.experiment_analysis?.variants]);

  const tocItems = useMemo(() => {
    if (!report) {
      return [];
    }
    const items = [
      { id: "story", label: t("researchReport.story.tocOverview") },
      { id: "chapter-sample", label: t("researchReport.story.tocSample") },
    ];
    if (report.sample.feedback > 0) {
      items.push({ id: "chapter-value", label: t("researchReport.story.tocValue") });
    }
    if ((report.algorithm_analysis?.algorithms?.length ?? 0) > 0) {
      items.push({ id: "chapter-algorithms", label: t("researchReport.story.tocAlgorithms") });
    }
    if (report.observability?.overall) {
      items.push({ id: "chapter-observability", label: t("researchReport.story.tocObservability") });
    }
    if (report.algorithm_analysis?.literature_suite) {
      items.push({ id: "chapter-literature", label: t("researchReport.story.tocLiterature") });
    }
    if (report.insight_analysis) {
      items.push({ id: "chapter-insights-deep", label: t("researchReport.story.tocInsightsDeep") });
    }
    if (report.survey_outcomes.count > 0) {
      items.push({ id: "chapter-satisfaction", label: t("researchReport.story.tocSatisfaction") });
    }
    if ((report.ranking_metrics.overall.run_count ?? 0) > 0) {
      items.push({ id: "chapter-ranking", label: t("researchReport.story.tocRanking") });
    }
    if (report.experiment_analysis) {
      items.push({ id: "chapter-experiment", label: t("researchReport.story.tocExperiment") });
    }
    items.push(
      { id: "chapter-evidence", label: t("researchReport.story.tocEvidence") },
      { id: "chapter-voice", label: t("researchReport.story.tocVoice") },
      { id: "chapter-appendix", label: t("researchReport.story.tocAppendix") },
    );
    return items;
  }, [report, t]);

  if (loading) {
    return (
      <PageShell>
        <LoadingSpinner label={t("researchReport.loading")} />
      </PageShell>
    );
  }

  if (error || !report || !narrative) {
    return (
      <PageShell>
        <PageHeader title={t("researchReport.title")} subtitle={t("researchReport.subtitle")} />
        <InlineAlert variant="danger">{error ?? t("researchReport.unavailable")}</InlineAlert>
      </PageShell>
    );
  }

  const ranking = report.ranking_metrics.overall;
  const hypothesisTests = report.experiment_analysis?.hypothesis_tests;
  const hasFeedback = report.sample.feedback > 0;
  const hasAlgorithms = (report.algorithm_analysis?.algorithms?.length ?? 0) > 0;
  let chapter = 0;
  const nextChapter = () => ++chapter;

  return (
    <PageShell pageClass="research-report-page">
      <div className="page-stack">
        <div className="research-report__hero">
          <PageHeader title={t("researchReport.title")} subtitle={t("researchReport.subtitle")} />
          <div className="research-report__meta">
            <span>{t("researchReport.generatedAt", { date: generatedLabel })}</span>
            <Link to="/admin/evaluation" className="research-report__back-link">
              {t("researchReport.backToInsights")}
            </Link>
          </div>
        </div>

        <ReportTableOfContents items={tocItems} />

        <StoryAtAGlance
          eyebrow={t("researchReport.story.atAGlance")}
          headline={narrative.headline}
          subheadline={narrative.subheadline}
        >
          {narrative.highlights.map((item) => (
            <StoryCard
              key={item.id}
              label={item.label}
              value={item.value}
              story={item.story}
              tone={item.tone}
            />
          ))}
        </StoryAtAGlance>

        <ReportChapter
          number={nextChapter()}
          id="chapter-sample"
          title={t("researchReport.story.chapter1Title")}
          lead={t("researchReport.story.chapter1Lead", {
            sessions: report.sample.sessions,
            runs: report.sample.runs,
            feedback: report.sample.feedback,
          })}
        >
          <StatGrid>
            <StatCard
              label={t("researchReport.sessions")}
              value={String(report.sample.sessions)}
              hint={t("researchReport.story.sessionsHint")}
            />
            <StatCard
              label={t("researchReport.runs")}
              value={String(report.sample.runs)}
              hint={t("researchReport.story.runsHint")}
            />
            <StatCard
              label={t("researchReport.feedback")}
              value={String(report.sample.feedback)}
              highlight
              hint={t("researchReport.story.feedbackHint")}
            />
            <StatCard
              label={t("researchReport.candidates")}
              value={String(report.sample.candidates)}
              hint={t("researchReport.story.candidatesHint")}
            />
          </StatGrid>
        </ReportChapter>

        {hasFeedback ? (
          <ReportChapter
            number={nextChapter()}
            id="chapter-value"
            title={t("researchReport.story.chapter2Title")}
            lead={t("researchReport.story.chapter2Lead")}
          >
            <StatGrid>
              <StatCard
                label={t("insights.avgEas")}
                value={formatDecimal(Number(report.primary_outcomes.average_eas ?? 0), locale)}
                highlight
                hint={t("researchReport.story.easHint")}
              />
              <StatCard
                label={t("insights.approvalRate")}
                value={formatPercent(Number(report.primary_outcomes.approval_rate ?? 0), locale)}
                hint={t("researchReport.story.approvalHint")}
              />
              <StatCard
                label={t("insights.wouldUseRate")}
                value={formatPercent(Number(report.primary_outcomes.would_use_rate ?? 0), locale)}
                hint={t("researchReport.story.wouldUseHint")}
              />
            </StatGrid>

            {narrative.topDimension && narrative.weakestDimension ? (
              <NarrativeCallout tone="neutral">
                <p className="mb-0">
                  {t("researchReport.story.dimensionStory", {
                    strongest: formatDimensionName(t, narrative.topDimension.name),
                    strongestScore: formatDecimal(narrative.topDimension.mean, locale),
                    weakest: formatDimensionName(t, narrative.weakestDimension.name),
                    weakestScore: formatDecimal(narrative.weakestDimension.mean, locale),
                  })}
                </p>
              </NarrativeCallout>
            ) : null}

            <CollapsibleBlock title={t("researchReport.story.ratingBreakdown")}>
              <DataTable
                columns={[
                  { key: "dimension", label: t("researchReport.dimension") },
                  { key: "mean", label: t("researchReport.mean"), align: "right" },
                  { key: "std", label: t("researchReport.std"), align: "right" },
                  { key: "count", label: "n", align: "right" },
                ]}
                rows={report.descriptive_statistics.map((row) => ({
                  dimension: formatDimensionName(t, row.dimension),
                  mean: formatDecimal(row.mean, locale),
                  std: formatDecimal(row.std, locale),
                  count: row.count,
                }))}
              />
              <div className="research-report__distribution-grid">
                {report.descriptive_statistics.map((row) => (
                  <DistributionBarChart
                    key={row.dimension}
                    label={formatDimensionName(t, row.dimension)}
                    distribution={row.distribution}
                  />
                ))}
              </div>
            </CollapsibleBlock>
          </ReportChapter>
        ) : null}

        {hasAlgorithms ? (
          <AlgorithmComparisonChapter report={report} locale={locale} chapterNumber={nextChapter()} />
        ) : null}

        {report.observability?.overall ? (
          <ObservabilityChapter report={report} locale={locale} chapterNumber={nextChapter()} />
        ) : null}

        {report.algorithm_analysis?.literature_suite ? (
          <LiteratureMetricsChapter report={report} locale={locale} chapterNumber={nextChapter()} />
        ) : null}

        {report.insight_analysis ? (
          <InsightAnalysisChapter report={report} locale={locale} chapterNumber={nextChapter()} />
        ) : null}

        {report.survey_outcomes.count > 0 ? (
          <ReportChapter
            number={nextChapter()}
            id="chapter-satisfaction"
            title={t("researchReport.story.chapter3Title")}
            lead={t("researchReport.story.chapter3Lead")}
          >
            <StatGrid>
              <StatCard
                label={t("researchReport.expectationMet")}
                value={formatDecimal(Number(report.survey_outcomes.expectation_met_mean ?? 0), locale)}
                hint={t("researchReport.story.expectationHint")}
              />
              <StatCard
                label={t("researchReport.wouldUseAgain")}
                value={formatPercent(Number(report.survey_outcomes.would_use_again_rate ?? 0), locale)}
              />
              <StatCard
                label={t("researchReport.wouldRecommend")}
                value={formatPercent(Number(report.survey_outcomes.would_recommend_rate ?? 0), locale)}
              />
            </StatGrid>
            <NarrativeCallout tone="positive">
              <p className="mb-0">{t("researchReport.story.satisfactionClosing")}</p>
            </NarrativeCallout>
          </ReportChapter>
        ) : null}

        {(ranking.run_count ?? 0) > 0 ? (
          <ReportChapter
            number={nextChapter()}
            id="chapter-ranking"
            title={t("researchReport.story.chapter4Title")}
            lead={t("researchReport.story.chapter4Lead")}
          >
            <NarrativeCallout tone={narrative.rankingTone}>
              <p className="mb-0">{narrative.rankingVerdict}</p>
            </NarrativeCallout>
            <StatGrid>
              <StatCard label="NDCG@5" value={formatDecimal(Number(ranking["ndcg@5"] ?? 0), locale)} highlight />
              <StatCard label="MAP" value={formatDecimal(Number(ranking.map ?? 0), locale)} />
              <StatCard label="MRR" value={formatDecimal(Number(ranking.mrr ?? 0), locale)} />
            </StatGrid>
            <CollapsibleBlock title={t("researchReport.story.rankingDetails")}>
              <p className="text-muted research-report__plain-note">{t("researchReport.rankingSubtitle")}</p>
              <StatGrid>
                <StatCard label="NDCG@3" value={formatDecimal(Number(ranking["ndcg@3"] ?? 0), locale)} />
                <StatCard
                  label={t("researchReport.spearman")}
                  value={
                    ranking.mean_spearman_rho != null
                      ? formatDecimal(Number(ranking.mean_spearman_rho), locale)
                      : "—"
                  }
                />
                <StatCard
                  label={t("researchReport.kendall")}
                  value={
                    ranking.mean_kendall_tau != null
                      ? formatDecimal(Number(ranking.mean_kendall_tau), locale)
                      : "—"
                  }
                />
              </StatGrid>
              {Object.keys(report.ranking_metrics.by_mode ?? {}).length > 0 ? (
                <DataTable
                  columns={[
                    { key: "mode", label: t("researchReport.mode") },
                    { key: "ndcg5", label: "NDCG@5", align: "right" },
                    { key: "map", label: "MAP", align: "right" },
                    { key: "runs", label: "n", align: "right" },
                  ]}
                  rows={Object.entries(report.ranking_metrics.by_mode).map(([mode, metrics]) => ({
                    mode,
                    ndcg5: formatDecimal(Number(metrics["ndcg@5"] ?? 0), locale),
                    map: formatDecimal(Number(metrics.map ?? 0), locale),
                    runs: metrics.run_count ?? 0,
                  }))}
                />
              ) : null}
            </CollapsibleBlock>
          </ReportChapter>
        ) : null}

        {report.experiment_analysis ? (
          <ReportChapter
            number={nextChapter()}
            id="chapter-experiment"
            title={t("researchReport.story.chapter5Title")}
            lead={t("researchReport.story.chapter5Lead")}
          >
            {narrative.experimentVerdict ? (
              <NarrativeCallout tone={narrative.experimentTone ?? "neutral"}>
                <p className="mb-0">{narrative.experimentVerdict}</p>
              </NarrativeCallout>
            ) : null}
            {experimentChartData.length > 0 ? (
              <GroupedBarChart
                data={experimentChartData}
                keys={["eas", "originality", "approval"]}
                labels={{
                  eas: t("insights.avgEas"),
                  originality: t("researchReport.originality"),
                  approval: t("insights.approvalRate"),
                }}
              />
            ) : null}
            <CollapsibleBlock title={t("researchReport.story.experimentDetails")}>
              <DataTable
                columns={[
                  { key: "variant", label: t("researchReport.variant") },
                  { key: "n", label: "n", align: "right" },
                  { key: "eas", label: t("insights.avgEas"), align: "right" },
                  { key: "approval", label: t("insights.approvalRate"), align: "right" },
                ]}
                rows={(report.experiment_analysis.variants ?? []).map((row) => ({
                  variant: String(row.variant),
                  n: Number(row.feedback_count ?? 0),
                  eas: formatDecimal(Number(row.average_eas ?? 0), locale),
                  approval: formatPercent(Number(row.approval_rate ?? 0), locale),
                }))}
              />
              {hypothesisTests ? (
                <div className="research-report__hypothesis-grid">
                  {Object.entries(hypothesisTests).map(([key, test]) => (
                    <HypothesisTestBlock
                      key={key}
                      title={t(`researchReport.tests.${key}`, key)}
                      test={test}
                      locale={locale}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-muted mb-0">{t("researchReport.noExperimentTests")}</p>
              )}
            </CollapsibleBlock>
          </ReportChapter>
        ) : null}

        <ReportChapter
          number={nextChapter()}
          id="chapter-evidence"
          title={t("researchReport.story.chapter6Title")}
          lead={t("researchReport.story.chapter6Lead")}
        >
          <StatGrid>
            <StatCard
              label={t("insights.sotaAnchorRate")}
              value={formatPercent(Number(report.sota_quality.sota_anchor_rate ?? 0), locale)}
              hint={t("researchReport.story.anchorHint")}
            />
            <StatCard
              label={t("insights.refinementRate")}
              value={formatPercent(Number(report.sota_quality.refinement_rate ?? 0), locale)}
              hint={t("researchReport.story.refinementHint")}
            />
            <StatCard
              label={t("insights.avgNoveltyVerified")}
              value={formatDecimal(Number(report.sota_quality.avg_novelty_verified ?? 0), locale)}
            />
          </StatGrid>
          {modeChartData.length > 0 ? (
            <CollapsibleBlock title={t("researchReport.story.modeComparisonDetails")}>
              <GroupedBarChart
                data={modeChartData}
                keys={["eas", "approval", "would_use"]}
                labels={{
                  eas: t("insights.avgEas"),
                  approval: t("insights.approvalRate"),
                  would_use: t("insights.wouldUseRate"),
                }}
              />
              <DataTable
                columns={[
                  { key: "mode", label: t("researchReport.mode") },
                  { key: "eas", label: t("insights.avgEas"), align: "right" },
                  { key: "approval", label: t("insights.approvalRate"), align: "right" },
                ]}
                rows={report.mode_comparison.map((row) => ({
                  mode: String(row.mode),
                  eas: formatDecimal(Number(row.average_eas ?? 0), locale),
                  approval: formatPercent(Number(row.approval_rate ?? 0), locale),
                }))}
                emptyMessage={t("researchReport.noModeData")}
              />
            </CollapsibleBlock>
          ) : null}
        </ReportChapter>

        <ReportChapter
          number={nextChapter()}
          id="chapter-voice"
          title={t("researchReport.story.chapter7Title")}
          lead={t("researchReport.story.chapter7Lead")}
        >
          {(report.weekly_trends?.length ?? 0) > 0 ? (
            <>
              <p className="research-report__plain-note">{t("researchReport.story.trendsNote")}</p>
              <TrendLineChart
                data={report.weekly_trends}
                dataKey="average_eas"
                label={t("insights.avgEas")}
              />
            </>
          ) : null}

          {report.rejection_summary.rejection_count > 0 ? (
            <NarrativeCallout tone="caution">
              <p className="mb-2">
                {t("researchReport.story.rejectionStory", {
                  rate: formatPercent(Number(report.rejection_summary.rejection_rate ?? 0), locale),
                  count: report.rejection_summary.rejection_count,
                })}
              </p>
              {report.rejection_summary.comments.length > 0 ? (
                <ul className="research-report__comments mb-0">
                  {report.rejection_summary.comments.slice(0, 5).map((comment, index) => (
                    <li key={index}>{comment}</li>
                  ))}
                </ul>
              ) : null}
            </NarrativeCallout>
          ) : (
            <NarrativeCallout tone="positive">
              <p className="mb-0">{t("researchReport.story.noRejections")}</p>
            </NarrativeCallout>
          )}

          {report.expert_label_analysis ? (
            <CollapsibleBlock title={t("researchReport.expertTitle")}>
              <StatGrid>
                <StatCard label="n" value={String(report.expert_label_analysis.n ?? 0)} />
                <StatCard
                  label={t("researchReport.spearman")}
                  value={
                    report.expert_label_analysis.spearman_rho != null
                      ? formatDecimal(Number(report.expert_label_analysis.spearman_rho), locale)
                      : "—"
                  }
                />
              </StatGrid>
            </CollapsibleBlock>
          ) : null}
        </ReportChapter>

        <ReportChapter
          number={nextChapter()}
          id="chapter-appendix"
          title={t("researchReport.story.chapter8Title")}
          lead={t("researchReport.story.chapter8Lead")}
        >
          <CollapsibleBlock title={t("researchReport.story.correlationDetails")}>
            <DataTable
              columns={[
                { key: "pair", label: t("researchReport.pair") },
                { key: "n", label: "n", align: "right" },
                { key: "spearman", label: t("researchReport.spearman"), align: "right" },
              ]}
              rows={report.score_correlations.map((row) => ({
                pair: String(row.pair),
                n: Number(row.n ?? 0),
                spearman: row.spearman_rho != null ? formatDecimal(Number(row.spearman_rho), locale) : "—",
              }))}
              emptyMessage={t("researchReport.noCorrelations")}
            />
          </CollapsibleBlock>
          <CollapsibleBlock title={t("researchReport.methodologyTitle")}>
            <dl className="research-report__methodology">
              <div>
                <dt>{t("researchReport.relevanceMapping")}</dt>
                <dd>{String(report.methodology_notes.relevance_mapping ?? "")}</dd>
              </div>
              <div>
                <dt>{t("researchReport.binaryThreshold")}</dt>
                <dd>{String(report.methodology_notes.binary_threshold ?? "")}</dd>
              </div>
              <div>
                <dt>{t("researchReport.primaryTest")}</dt>
                <dd>{String(report.methodology_notes.primary_test ?? "")}</dd>
              </div>
              {report.primary_outcomes.cronbach_alpha != null ? (
                <div>
                  <dt>{t("researchReport.cronbachAlpha")}</dt>
                  <dd>
                    {formatDecimal(Number(report.primary_outcomes.cronbach_alpha), locale)} —{" "}
                    {t("researchReport.cronbachHint")}
                  </dd>
                </div>
              ) : null}
            </dl>
          </CollapsibleBlock>
        </ReportChapter>
      </div>
    </PageShell>
  );
}
