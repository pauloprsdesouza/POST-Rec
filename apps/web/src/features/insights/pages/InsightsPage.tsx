import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { PageHeader } from "@/shared/ui/PageHeader";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { ValidationDashboard } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";
import { GroupedBarChart, TrendLineChart } from "@/features/insights/components/InsightCharts";

function InsightMetric({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`insight-metric ${highlight ? "insight-metric--highlight" : ""}`}>
      <span className="insight-metric__label">{label}</span>
      <span className="insight-metric__value">{value}</span>
    </div>
  );
}

function InsightSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="insight-section panel">
      <div className="panel__header">
        <h2 className="panel__title">{title}</h2>
      </div>
      <div className="insight-section__grid">{children}</div>
    </section>
  );
}

export function InsightsPage() {
  const { t, i18n } = useTranslation();
  const { accessToken } = useAuth();
  const [dashboard, setDashboard] = useState<ValidationDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const locale = i18n.language;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    adminService
      .getEvaluationDashboard(accessToken)
      .then(setDashboard)
      .catch((err) => setError(err instanceof Error ? err.message : t("common.couldNotLoadMetrics")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

  const experimentChartData = useMemo(() => {
    const variants = dashboard?.experiment?.variants ?? [];
    return variants.map((variant) => ({
      label: variant.variant,
      eas: variant.average_eas,
      approval: variant.approval_rate * 100,
      would_use: variant.would_use_rate * 100,
    }));
  }, [dashboard?.experiment?.variants]);

  if (loading) {
    return (
      <div className="page-shell">
        <LoadingSpinner label={t("common.loadingInsights")} />
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="page-shell">
        <PageHeader title={t("insights.title")} subtitle={t("insights.subtitle")} />
        <InlineAlert variant="danger">{error ?? t("common.metricsUnavailable")}</InlineAlert>
      </div>
    );
  }

  const hasFeedback = dashboard.total_feedback > 0;
  const survey = dashboard.survey_metrics;
  const ranking = dashboard.ranking_summary;

  return (
    <div className="page-shell insights-page">
      <div className="page-stack">
        <div data-coach="coach-insights-overview" className="insights-coach-target">
          <PageHeader
            title={t("admin.evaluation.title")}
            subtitle={t("admin.evaluation.subtitle")}
          />
          <div className="insights-page__actions">
            <Link to="/admin/research-report" className="btn btn-primary">
              {t("insights.viewFullReport")}
            </Link>
          </div>

          {!hasFeedback ? (
            <EmptyState
              variant="insights"
              title={t("insights.emptyTitle")}
              description={t("insights.emptyDescription")}
              action={
                <Link to="/runs/new" className="btn btn-primary">
                  {t("insights.emptyAction")}
                </Link>
              }
            />
          ) : (
            <InsightSection title={t("insights.quality")}>
              <InsightMetric
                label={t("insights.avgEas")}
                value={formatDecimal(dashboard.average_eas, locale)}
                highlight
              />
              <InsightMetric
                label={t("insights.approvalRate")}
                value={formatPercent(dashboard.approval_rate, locale)}
              />
              <InsightMetric
                label={t("insights.wouldUseRate")}
                value={formatPercent(dashboard.would_use_rate, locale)}
              />
              <InsightMetric
                label={t("insights.failureRate")}
                value={formatPercent(dashboard.run_failure_rate, locale)}
              />
            </InsightSection>
          )}
        </div>

        <InsightSection title={t("insights.trustFeasibility")}>
          <InsightMetric
            label={t("insights.avgTrust")}
            value={formatDecimal(dashboard.average_trust_score, locale)}
          />
          <InsightMetric
            label={t("insights.avgFeasibility")}
            value={formatDecimal(dashboard.average_feasibility_score, locale)}
          />
          <InsightMetric
            label={t("insights.avgUsefulness")}
            value={formatDecimal(dashboard.average_usefulness_score, locale)}
          />
        </InsightSection>

        {survey && survey.count > 0 ? (
          <InsightSection title={t("insights.survey")}>
            <InsightMetric
              label={t("insights.expectationMet")}
              value={formatDecimal(survey.expectation_met_mean, locale)}
            />
            <InsightMetric
              label={t("insights.wouldUseAgain")}
              value={formatPercent(survey.would_use_again_rate, locale)}
            />
            <InsightMetric
              label={t("insights.wouldRecommend")}
              value={formatPercent(survey.would_recommend_rate, locale)}
            />
            <InsightMetric label={t("insights.surveyCount")} value={String(survey.count)} />
          </InsightSection>
        ) : null}

        <InsightSection title={t("insights.sotaQuality")}>
          <InsightMetric
            label={t("insights.sotaAnchorRate")}
            value={formatPercent(dashboard.sota_anchor_rate ?? 0, locale)}
          />
          <InsightMetric
            label={t("insights.refinementRate")}
            value={formatPercent(dashboard.refinement_rate ?? 0, locale)}
          />
          <InsightMetric
            label={t("insights.avgNoveltyVerified")}
            value={formatDecimal(dashboard.avg_novelty_verified ?? 0, locale)}
          />
          <InsightMetric
            label={t("insights.avgSotaFit")}
            value={formatDecimal(dashboard.avg_sota_fit ?? 0, locale)}
          />
        </InsightSection>

        {ranking && (ranking.run_count ?? 0) > 0 ? (
          <section className="insight-section panel">
            <div className="panel__header">
              <h2 className="panel__title">{t("insights.rankingMetrics")}</h2>
            </div>
            <div className="insight-section__grid">
              <InsightMetric label="NDCG@5" value={formatDecimal(ranking["ndcg@5"] ?? 0, locale)} highlight />
              <InsightMetric label="MAP" value={formatDecimal(ranking.map ?? 0, locale)} />
              <InsightMetric label="MRR" value={formatDecimal(ranking.mrr ?? 0, locale)} />
              <InsightMetric
                label={t("insights.spearman")}
                value={
                  ranking.mean_spearman_rho != null
                    ? formatDecimal(ranking.mean_spearman_rho, locale)
                    : "—"
                }
              />
            </div>
          </section>
        ) : null}

        {dashboard.experiment && dashboard.experiment.variants.length > 0 ? (
          <section className="insight-section panel">
            <div className="panel__header">
              <h2 className="panel__title">{t("insights.experiment")}</h2>
              <p className="panel__subtitle text-muted mb-0">{dashboard.experiment.experiment_id}</p>
            </div>
            <div className="insight-section__grid">
              {dashboard.experiment.variants.map((variant) => (
                <InsightMetric
                  key={variant.variant}
                  label={`${variant.variant} · EAS`}
                  value={formatDecimal(variant.average_eas, locale)}
                  highlight={variant.variant === "treatment"}
                />
              ))}
              {dashboard.experiment.variants.map((variant) => (
                <InsightMetric
                  key={`${variant.variant}-approval`}
                  label={`${variant.variant} · ${t("insights.approvalRate")}`}
                  value={formatPercent(variant.approval_rate, locale)}
                />
              ))}
            </div>
            {experimentChartData.length > 0 ? (
              <GroupedBarChart
                data={experimentChartData}
                keys={["eas", "approval", "would_use"]}
                labels={{
                  eas: t("insights.avgEas"),
                  approval: t("insights.approvalRate"),
                  would_use: t("insights.wouldUseRate"),
                }}
              />
            ) : null}
          </section>
        ) : null}

        {(dashboard.weekly_trends?.length ?? 0) > 0 ? (
          <section className="insight-section panel">
            <div className="panel__header">
              <h2 className="panel__title">{t("insights.trends")}</h2>
            </div>
            <TrendLineChart
              data={dashboard.weekly_trends ?? []}
              dataKey="average_eas"
              label={t("insights.avgEas")}
            />
          </section>
        ) : null}

        <InsightSection title={t("insights.activity")}>
          <InsightMetric
            label={t("insights.totalRuns")}
            value={String(dashboard.total_runs)}
            highlight
          />
          <InsightMetric label={t("insights.totalFeedback")} value={String(dashboard.total_feedback)} />
          <InsightMetric
            label={t("insights.completionRate")}
            value={formatPercent(dashboard.run_completion_rate, locale)}
          />
        </InsightSection>
      </div>
    </div>
  );
}
