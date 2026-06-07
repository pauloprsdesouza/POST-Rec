import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

interface AuthShellProps {
  children: ReactNode;
  online: boolean | null;
}

export function AuthShell({ online, children }: AuthShellProps) {
  const { t } = useTranslation();

  const apiBadge =
    online === null
      ? t("common.apiChecking")
      : online
        ? t("common.apiOnline")
        : t("common.apiOffline");

  return (
    <div className="auth-shell min-vh-100">
      <div className="auth-shell__panel auth-shell__panel--brand">
        <div className="auth-shell__brand-inner">
          <p className="auth-shell__eyebrow">{t("auth.eyebrow")}</p>
          <h1 className="auth-shell__title">{t("auth.heroTitle")}</h1>
          <p className="auth-shell__subtitle">{t("auth.heroSubtitle")}</p>
          <ul className="auth-shell__features">
            <li>{t("auth.feature1")}</li>
            <li>{t("auth.feature2")}</li>
            <li>{t("auth.feature3")}</li>
          </ul>
        </div>
      </div>
      <div className="auth-shell__panel auth-shell__panel--form">
        <div className="auth-shell__form-inner">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <span className="auth-shell__logo">{t("common.appName")}</span>
            <span
              className={`badge ${online ? "text-bg-success" : online === false ? "text-bg-danger" : "text-bg-secondary"}`}
            >
              {apiBadge}
            </span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
