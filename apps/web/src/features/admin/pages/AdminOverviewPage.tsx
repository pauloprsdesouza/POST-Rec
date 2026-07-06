import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { AdminOverview } from "@/shared/types/api";
import { formatDecimal, formatPercent } from "@/features/runs/utils/runs";
import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { Panel } from "@/shared/ui/Panel";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

function MetricCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Panel className="admin-metric">
      <span className="admin-metric__label">{label}</span>
      <span className="admin-metric__value">{value}</span>
      {hint ? <span className="admin-metric__hint text-muted">{hint}</span> : null}
    </Panel>
  );
}

function HealthCheckList({ checks }: { checks: Record<string, string> }) {
  return (
    <ul className="admin-health-list">
      {Object.entries(checks).map(([name, status]) => {
        const ok = status === "ok" || status.startsWith("ok (") || status.startsWith("warning");
        return (
          <li key={name} className={`admin-health-list__item${ok ? "" : " admin-health-list__item--fail"}`}>
            <span className="admin-health-list__name">{name}</span>
            <span className="admin-health-list__status">{status}</span>
          </li>
        );
      })}
    </ul>
  );
}

export function AdminOverviewPage() {
  const { t, i18n } = useTranslation();
  const { accessToken } = useAuth();
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const locale = i18n.language;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    adminService
      .getOverview(accessToken)
      .then(setOverview)
      .catch((err) => setError(err instanceof Error ? err.message : t("admin.loadError")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

  if (loading) {
    return <LoadingSpinner label={t("admin.loading")} />;
  }

  if (error || !overview) {
    return <InlineAlert variant="danger">{error ?? t("admin.loadError")}</InlineAlert>;
  }

  return (
    <PageShell pageClass="admin-page">
      <PageHeader title={t("admin.overview.title")} subtitle={t("admin.overview.subtitle")} />

      <div className="admin-page__actions">
        <Link to="/admin/evaluation" className="btn btn-outline-primary btn-sm">
          {t("admin.overview.openEvaluation")}
        </Link>
        <Link to="/admin/research-report" className="btn btn-outline-primary btn-sm">
          {t("admin.overview.openReport")}
        </Link>
      </div>

      <section className="admin-section">
        <h2 className="admin-section__title">{t("admin.overview.platform")}</h2>
        <div className="admin-metric-grid">
          <MetricCard label={t("admin.overview.users")} value={String(overview.users.total)} />
          <MetricCard label={t("admin.overview.activeUsers")} value={String(overview.users.active)} />
          <MetricCard label={t("admin.overview.admins")} value={String(overview.users.admins)} />
          <MetricCard
            label={t("admin.overview.totalRuns")}
            value={String(overview.runs.total)}
            hint={t("admin.overview.completionHint", {
              rate: formatPercent(overview.runs.completion_rate, locale),
            })}
          />
          <MetricCard label={t("admin.overview.feedback")} value={String(overview.feedback_total)} />
          <MetricCard
            label={t("admin.overview.llmCost")}
            value={`$${formatDecimal(overview.llm_cost_usd_total, locale, 2)}`}
          />
        </div>
      </section>

      <Panel
        as="section"
        className="admin-section"
        title={t("admin.overview.systemHealth")}
        headingLevel="h2"
        headerExtra={
          <span
            className={`admin-status-pill admin-status-pill--${overview.system_status === "ready" ? "ok" : "warn"}`}
          >
            {overview.system_status}
          </span>
        }
      >
        <p className="text-muted mb-3">
          {t("admin.overview.environment")}: <strong>{overview.app_env}</strong>
        </p>
        <HealthCheckList checks={overview.health_checks} />
      </Panel>
    </PageShell>
  );
}
