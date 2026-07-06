import { useMemo } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { NavIcon } from "@/shared/ui/NavIcons";

type BottomNavItem = {
  to: string;
  labelKey: "nav.runs" | "nav.new" | "nav.admin" | "nav.profile";
  icon: "runs" | "new" | "insights" | "profile";
  match: (path: string) => boolean;
  primary: boolean;
};

export function MobileBottomNav() {
  const { t } = useTranslation();
  const { consentDone, profileDone, isAdmin } = useAuth();
  const { pathname } = useLocation();
  const setupComplete = consentDone && profileDone;

  const mainItems = useMemo((): BottomNavItem[] => {
    const items: BottomNavItem[] = [
      {
        to: "/runs",
        labelKey: "nav.runs",
        icon: "runs",
        match: (path: string) => path === "/runs" || /^\/runs\/[^/]+/.test(path),
        primary: false,
      },
      {
        to: "/runs/new",
        labelKey: "nav.new",
        icon: "new",
        match: (path: string) => path === "/runs/new",
        primary: true,
      },
    ];

    if (isAdmin) {
      items.push({
        to: "/admin",
        labelKey: "nav.admin",
        icon: "insights",
        match: (path: string) => path.startsWith("/admin"),
        primary: false,
      });
    }

    items.push({
      to: "/profile",
      labelKey: "nav.profile",
      icon: "profile",
      match: (path: string) => path.startsWith("/profile"),
      primary: false,
    });

    return items;
  }, [isAdmin]);

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
          <span className="bottom-nav__icon-slot">
            <NavIcon name="setup" />
          </span>
          <span className="bottom-nav__label">{t("nav.completeSetup")}</span>
        </NavLink>
        <NavLink
          to="/how-it-works"
          className={`bottom-nav__item ${pathname.startsWith("/how-it-works") ? "bottom-nav__item--active" : ""}`}
        >
          <span className="bottom-nav__icon-slot">
            <NavIcon name="help" />
          </span>
          <span className="bottom-nav__label">{t("nav.howItWorks")}</span>
        </NavLink>
      </nav>
    );
  }

  return (
    <nav className="bottom-nav d-lg-none" aria-label={t("nav.mainNavigation")} data-coach="coach-bottom-nav">
      {mainItems.map((item) => {
        const active = item.match(pathname);
        const classNames = [
          "bottom-nav__item",
          active ? "bottom-nav__item--active" : "",
          item.primary ? "bottom-nav__item--primary" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/runs"}
            className={classNames}
            {...(item.primary ? { "data-coach": "coach-runs-new-run" } : {})}
          >
            <span className="bottom-nav__icon-slot">
              {item.primary ? (
                <span className="bottom-nav__fab">
                  <NavIcon name={item.icon} />
                </span>
              ) : (
                <NavIcon name={item.icon} />
              )}
            </span>
            <span className="bottom-nav__label">{t(item.labelKey)}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
