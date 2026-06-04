import { Dropdown, Nav, Navbar } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext";
import { useApiHealth } from "../../hooks/useApiHealth";
import { LanguageSwitcher } from "../ui/LanguageSwitcher";
import { MobileBottomNav } from "./MobileBottomNav";
import { SetupBanner } from "./SetupBanner";

const DESKTOP_NAV = [
  { to: "/runs/new", labelKey: "nav.newRun" as const },
  { to: "/runs", labelKey: "nav.runs" as const },
  { to: "/how-it-works", labelKey: "nav.howItWorks" as const },
  { to: "/insights", labelKey: "nav.insights" as const },
] as const;

export function AppLayout() {
  const { t } = useTranslation();
  const { user, signOut, consentDone, profileDone } = useAuth();
  const online = useApiHealth();
  const navigate = useNavigate();

  const setupComplete = consentDone && profileDone;
  const displayName = user?.fullName?.split(" ")[0] ?? t("common.researcher");

  const apiTitle =
    online === null ? t("common.apiChecking") : online ? t("common.apiOnline") : t("common.apiOffline");

  return (
    <>
      <Navbar expand="lg" variant="dark" className="app-navbar shadow-sm sticky-top">
        <div className="container-fluid container-lg">
          <Navbar.Brand as={Link} to="/" className="app-brand">
            <span className="app-brand__mark">P</span>
            <span className="app-brand__text">{t("common.appName")}</span>
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="main-nav" />
          <Navbar.Collapse id="main-nav">
            <Nav className="me-auto app-nav d-none d-lg-flex">
              {setupComplete ? (
                DESKTOP_NAV.map((item) => (
                  <Nav.Link as={NavLink} to={item.to} key={item.to} end={item.to === "/runs"}>
                    {t(item.labelKey)}
                  </Nav.Link>
                ))
              ) : (
                <Nav.Link as={NavLink} to="/profile" className="text-warning-emphasis">
                  {t("nav.completeSetup")}
                </Nav.Link>
              )}
            </Nav>

            <div className="d-flex align-items-center gap-2 py-2 py-lg-0">
              <LanguageSwitcher variant="navbar" />

              <span
                className={`api-pill ${online ? "api-pill--online" : online === false ? "api-pill--offline" : ""}`}
                title={apiTitle}
              />

              <Dropdown align="end" className="user-dropdown">
                <Dropdown.Toggle variant="link" className="user-dropdown__toggle text-decoration-none">
                  <span className="user-dropdown__avatar">{displayName.charAt(0).toUpperCase()}</span>
                  <span className="d-none d-md-inline user-dropdown__name">{displayName}</span>
                </Dropdown.Toggle>
                <Dropdown.Menu className="user-dropdown__menu shadow">
                  <Dropdown.Header className="user-dropdown__header">
                    <div className="fw-semibold">{user?.fullName ?? t("common.researcher")}</div>
                    <div className="small text-secondary">{user?.email ?? user?.phoneNumber}</div>
                  </Dropdown.Header>
                  <Dropdown.Divider />
                  <Dropdown.Item as={Link} to="/profile?tab=account">
                    {t("nav.account")}
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/profile?tab=research">
                    {t("nav.researchProfile")}
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/profile?tab=preferences">
                    {t("nav.preferences")}
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/how-it-works">
                    {t("nav.howItWorks")}
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/profile?tab=consent">
                    {t("nav.consent")}
                  </Dropdown.Item>
                  <Dropdown.Divider />
                  <Dropdown.Item
                    onClick={() => {
                      signOut();
                      navigate("/sign-in");
                    }}
                  >
                    {t("nav.signOut")}
                  </Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            </div>
          </Navbar.Collapse>
        </div>
      </Navbar>

      <main className="app-main app-main--with-bottom-nav">
        <div className="container-fluid container-lg">
          <SetupBanner />
          <Outlet />
        </div>
      </main>

      <MobileBottomNav />
    </>
  );
}
