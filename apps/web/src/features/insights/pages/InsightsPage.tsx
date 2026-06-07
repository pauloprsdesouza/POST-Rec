import { useEffect, useState, type ReactNode } from "react";
import { Alert } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { PageHeader } from "@/shared/ui/PageHeader";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { useAuth } from "@/features/auth/context/AuthContext";
import { validationService } from "@/shared/api";
import type { ValidationDashboard } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";

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
    <section className="insight-section">
      <h2 className="insight-section__title">{title}</h2>
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
    validationService
      .getDashboard(accessToken)
      .then(setDashboard)
      .catch((err) => setError(err instanceof Error ? err.message : t("common.couldNotLoadMetrics")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

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
        <Alert variant="danger">{error ?? t("common.metricsUnavailable")}</Alert>
      </div>
    );
  }

  const hasFeedback = dashboard.total_feedback > 0;

  return (
    <div className="page-shell insights-page">
      <PageHeader title={t("insights.title")} subtitle={t("insights.subtitle")} />

      {!hasFeedback ? (
        <p className="insights-page__hint">{t("insights.emptyHint")}</p>
      ) : null}

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
  );
}
