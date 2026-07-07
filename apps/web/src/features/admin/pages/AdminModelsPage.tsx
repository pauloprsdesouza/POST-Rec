import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { AdminModelEvaluation } from "@/shared/types/api";
import { formatDecimal } from "@/features/runs/utils/runs";
import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { Panel } from "@/shared/ui/Panel";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

export function AdminModelsPage() {
  const { t, i18n } = useTranslation();
  const { accessToken } = useAuth();
  const [data, setData] = useState<AdminModelEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const locale = i18n.language;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    adminService
      .getModelEvaluation(accessToken)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : t("admin.loadError")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

  if (loading) {
    return (
      <PageShell pageClass="admin-page">
        <div className="page-stack page-stack--tight">
          <LoadingSpinner label={t("admin.loading")} />
        </div>
      </PageShell>
    );
  }

  if (error || !data) {
    return (
      <PageShell pageClass="admin-page">
        <div className="page-stack page-stack--tight">
          <InlineAlert variant="danger">{error ?? t("admin.loadError")}</InlineAlert>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell pageClass="admin-page">
      <div className="page-stack page-stack--tight">
        <PageHeader title={t("admin.models.title")} subtitle={t("admin.models.subtitle")} />

        <Panel as="section" className="admin-section">
          <h2 className="admin-section__title">{t("admin.models.configured")}</h2>
          <dl className="admin-config-list">
            <div>
              <dt>{t("admin.models.generation")}</dt>
              <dd>{data.configured_models.generation}</dd>
            </div>
            <div>
              <dt>{t("admin.models.embedding")}</dt>
              <dd>
                {data.configured_models.embedding} ({data.configured_models.embedding_dimensions}d)
              </dd>
            </div>
          </dl>
        </Panel>

        <section className="admin-section">
          <h2 className="admin-section__title">{t("admin.models.usage")}</h2>
          <div className="admin-metric-grid">
            <Panel className="admin-metric">
              <span className="admin-metric__label">{t("admin.models.calls")}</span>
              <span className="admin-metric__value">{data.aggregate.call_count}</span>
            </Panel>
            <Panel className="admin-metric">
              <span className="admin-metric__label">{t("admin.models.tokens")}</span>
              <span className="admin-metric__value">{data.aggregate.total_tokens.toLocaleString(locale)}</span>
            </Panel>
            <Panel className="admin-metric">
              <span className="admin-metric__label">{t("admin.models.cost")}</span>
              <span className="admin-metric__value">
                ${formatDecimal(data.aggregate.estimated_cost_usd, locale, 2)}
              </span>
            </Panel>
          </div>
        </section>

        <Panel as="section" className="admin-section">
          <h2 className="admin-section__title">{t("admin.models.byModel")}</h2>
          <div className="table-responsive">
            <table className="table table-sm admin-table">
              <thead>
                <tr>
                  <th>{t("admin.models.tableModel")}</th>
                  <th>{t("admin.models.calls")}</th>
                  <th>{t("admin.models.tokens")}</th>
                  <th>{t("admin.models.cost")}</th>
                </tr>
              </thead>
              <tbody>
                {data.models.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-muted">
                      {t("admin.models.empty")}
                    </td>
                  </tr>
                ) : (
                  data.models.map((row) => (
                    <tr key={`${row.provider}/${row.model}`}>
                      <td data-label={t("admin.models.tableModel")}>
                        <span className="admin-table__primary">{row.model}</span>
                        <span className="admin-table__secondary">{row.provider}</span>
                      </td>
                      <td data-label={t("admin.models.calls")}>{row.call_count}</td>
                      <td data-label={t("admin.models.tokens")}>
                        {row.total_tokens.toLocaleString(locale)}
                      </td>
                      <td data-label={t("admin.models.cost")}>
                        ${formatDecimal(row.estimated_cost_usd, locale, 4)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </PageShell>
  );
}
