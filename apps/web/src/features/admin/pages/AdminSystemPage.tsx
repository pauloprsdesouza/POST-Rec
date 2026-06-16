import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { AdminSystemConfig } from "@/shared/types/api";
import { PageHeader } from "@/shared/ui/PageHeader";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

function formatConfigValue(value: string | number | boolean): string {
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

export function AdminSystemPage() {
  const { t } = useTranslation();
  const { accessToken } = useAuth();
  const [config, setConfig] = useState<AdminSystemConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    adminService
      .getSystemConfig(accessToken)
      .then(setConfig)
      .catch((err) => setError(err instanceof Error ? err.message : t("admin.loadError")))
      .finally(() => setLoading(false));
  }, [accessToken, t]);

  if (loading) {
    return <LoadingSpinner label={t("admin.loading")} />;
  }

  if (error || !config) {
    return <InlineAlert variant="danger">{error ?? t("admin.loadError")}</InlineAlert>;
  }

  const entries = Object.entries(config.environment).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="page-shell admin-page">
      <PageHeader title={t("admin.system.title")} subtitle={t("admin.system.subtitle")} />

      <section className="admin-section panel">
        <p className="text-muted">{t("admin.system.readOnlyNote")}</p>
        <dl className="admin-config-list admin-config-list--grid">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{formatConfigValue(value)}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
