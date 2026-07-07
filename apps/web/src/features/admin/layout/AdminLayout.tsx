import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { Panel } from "@/shared/ui/Panel";

const ADMIN_NAV = [
  { to: "/admin", labelKey: "admin.nav.overview", end: true },
  { to: "/admin/evaluation", labelKey: "admin.nav.evaluation", end: false },
  { to: "/admin/models", labelKey: "admin.nav.models", end: false },
  { to: "/admin/system", labelKey: "admin.nav.system", end: false },
  { to: "/admin/users", labelKey: "admin.nav.users", end: false },
] as const;

export function AdminLayout() {
  const { t } = useTranslation();

  return (
    <div className="admin-shell">
      <Panel as="aside" className="admin-shell__sidebar" aria-label={t("admin.sidebarLabel")}>
        <div className="admin-shell__brand">
          <span className="admin-shell__badge">{t("admin.badge")}</span>
          <h1 className="admin-shell__title">{t("admin.title")}</h1>
        </div>
        <nav className="admin-shell__nav">
          {ADMIN_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `admin-shell__link${isActive ? " admin-shell__link--active" : ""}`
              }
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
          <NavLink to="/runs" className="admin-shell__link admin-shell__link--workspace">
            {t("admin.backToResearch")}
          </NavLink>
        </nav>
      </Panel>
      <div className="admin-shell__content">
        <Outlet />
      </div>
    </div>
  );
}
