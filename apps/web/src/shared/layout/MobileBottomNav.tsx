import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { NavIcon } from "@/shared/ui/NavIcons";

const MAIN_ITEMS = [
  {
    to: "/runs",
    labelKey: "nav.runs" as const,
    icon: "runs" as const,
    match: (path: string) => path === "/runs" || /^\/runs\/[^/]+/.test(path),
    primary: false,
  },
  {
    to: "/runs/new",
    labelKey: "nav.new" as const,
    icon: "new" as const,
    match: (path: string) => path === "/runs/new",
    primary: true,
  },
  {
    to: "/insights",
    labelKey: "nav.insights" as const,
    icon: "insights" as const,
    match: (path: string) => path.startsWith("/insights"),
    primary: false,
  },
  {
    to: "/profile",
    labelKey: "nav.profile" as const,
    icon: "profile" as const,
    match: (path: string) => path.startsWith("/profile"),
    primary: false,
  },
] as const;

export function MobileBottomNav() {
  const { t } = useTranslation();
  const { consentDone, profileDone } = useAuth();
  const { pathname } = useLocation();
  const setupComplete = consentDone && profileDone;

  if (!setupComplete) {
    const setupTo = !consentDone ? "/consent" : "/profile?tab=research";
    const setupActive =
      pathname.startsWith("/consent") ||
      (pathname.startsWith("/profile") && !profileDone);

    return (
      <nav className="bottom-nav d-lg-none" aria-label={t("nav.mainNavigation")}>
        <NavLink
          to={setupTo}
          className={`bottom-nav__item bottom-nav__item--setup ${setupActive ? "bottom-nav__item--active" : ""}`}
        >
          <NavIcon name="setup" />
          <span className="bottom-nav__label">{t("nav.completeSetup")}</span>
        </NavLink>
        <NavLink
          to="/how-it-works"
          className={`bottom-nav__item ${pathname.startsWith("/how-it-works") ? "bottom-nav__item--active" : ""}`}
        >
          <NavIcon name="help" />
          <span className="bottom-nav__label">{t("nav.howItWorks")}</span>
        </NavLink>
      </nav>
    );
  }

  return (
    <nav className="bottom-nav d-lg-none" aria-label={t("nav.mainNavigation")}>
      {MAIN_ITEMS.map((item) => {
        const active = item.match(pathname);
        const classNames = [
          "bottom-nav__item",
          active ? "bottom-nav__item--active" : "",
          item.primary ? "bottom-nav__item--primary" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <NavLink key={item.to} to={item.to} end={item.to === "/runs"} className={classNames}>
            <span className={item.primary ? "bottom-nav__fab" : undefined}>
              <NavIcon name={item.icon} />
            </span>
            <span className="bottom-nav__label">{t(item.labelKey)}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
