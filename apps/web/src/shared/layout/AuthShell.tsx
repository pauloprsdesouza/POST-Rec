import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "@/shared/ui/LanguageSwitcher";
import { ThemeToggle } from "@/shared/ui/ThemeToggle";

interface AuthShellProps {
  children: ReactNode;
  online: boolean | null;
}

export function AuthShell({ children, online }: AuthShellProps) {
  const { t } = useTranslation();

  return (
    <div className="auth-shell min-vh-100">
      <header className="auth-shell__topbar">
        <span className="auth-shell__logo">
          <span className="auth-shell__logo-mark" aria-hidden="true">R</span>
          <span className="auth-shell__logo-text">{t("common.appName")}</span>
        </span>
        <div className="auth-shell__topbar-actions">
          <ThemeToggle variant="navbar" />
          <LanguageSwitcher variant="navbar" />
          {online === false ? (
            <span className="api-pill api-pill--offline" role="status">
              <span className="api-pill__dot" aria-hidden />
              <span className="api-pill__label">{t("common.apiOffline")}</span>
            </span>
          ) : null}
        </div>
      </header>

      <div className="auth-shell__body">
        <aside className="auth-shell__panel auth-shell__panel--brand" aria-label={t("auth.brandPanelLabel")}>
          <div className="auth-shell__brand-inner">
            <p className="auth-shell__eyebrow">{t("auth.eyebrow")}</p>
            <h1 className="auth-shell__title">{t("auth.heroTitle")}</h1>
            <p className="auth-shell__lead">{t("auth.heroSubtitle")}</p>
            <ul className="auth-shell__features">
              <li>{t("auth.feature1")}</li>
              <li>{t("auth.feature2")}</li>
              <li>{t("auth.feature3")}</li>
            </ul>
            <p className="auth-shell__trust">{t("auth.trustLine")}</p>
          </div>
        </aside>

        <div className="auth-shell__panel auth-shell__panel--form">
          <div className="auth-shell__form-inner">{children}</div>
        </div>
      </div>
    </div>
  );
}
