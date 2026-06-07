import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";

const ITEMS = [
  { to: "/runs/new", labelKey: "nav.new" as const, match: (path: string) => path === "/runs/new" },
  {
    to: "/runs",
    labelKey: "nav.runs" as const,
    match: (path: string) => path === "/runs" || /^\/runs\/[^/]+/.test(path),
  },
  { to: "/profile", labelKey: "nav.profile" as const, match: (path: string) => path.startsWith("/profile") },
  { to: "/insights", labelKey: "nav.insights" as const, match: (path: string) => path.startsWith("/insights") },
] as const;

export function MobileBottomNav() {
  const { t } = useTranslation();
  const { consentDone, profileDone } = useAuth();
  const { pathname } = useLocation();
  const setupComplete = consentDone && profileDone;

  if (!setupComplete) {
    return null;
  }

  return (
    <nav className="bottom-nav d-lg-none" aria-label={t("nav.mainNavigation")}>
      {ITEMS.map((item) => {
        const active = item.match(pathname);
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={`bottom-nav__item ${active ? "bottom-nav__item--active" : ""}`}
          >
            <span className="bottom-nav__label">{t(item.labelKey)}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
