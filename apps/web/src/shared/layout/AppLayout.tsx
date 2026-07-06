import { useCallback, useState } from "react";
import { Dropdown, Nav, Navbar } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { useCoachMarks } from "@/shared/coachmarks/CoachMarkProvider";
import { usePwaMode } from "@/shared/pwa/PwaModeProvider";
import { LanguageSwitcher } from "@/shared/ui/LanguageSwitcher";
import { ThemeToggle } from "@/shared/ui/ThemeToggle";
import { MobileBottomNav } from "./MobileBottomNav";
import { PwaInstallBanner } from "./PwaInstallBanner";
import { SetupBanner } from "./SetupBanner";

const DESKTOP_NAV = [
  { to: "/runs/new", labelKey: "nav.newRun" as const },
  { to: "/runs", labelKey: "nav.runs" as const },
  { to: "/how-it-works", labelKey: "nav.howItWorks" as const },
] as const;

export function AppLayout() {
  const { t } = useTranslation();
  const { user, signOut, consentDone, profileDone, isAdmin } = useAuth();
  const { startTourForCurrentPage, resetTours } = useCoachMarks();
  const navigate = useNavigate();
  const isPwaMode = usePwaMode();
  const [navExpanded, setNavExpanded] = useState(false);

  const setupComplete = consentDone && profileDone;
  const setupHref = !consentDone ? "/consent" : "/profile?tab=research";
  const displayName = user?.fullName?.split(" ")[0] ?? t("common.researcher");

  const closeNav = useCallback(() => setNavExpanded(false), []);

  const primaryNavLinks = setupComplete ? (
    <>
      {DESKTOP_NAV.map((item) => (
        <Nav.Link
          as={NavLink}
          to={item.to}
          key={item.to}
          end={item.to === "/runs"}
          onClick={closeNav}
          {...(item.to === "/runs/new" ? { "data-coach": "coach-nav-new-run" } : {})}
        >
          {t(item.labelKey)}
        </Nav.Link>
      ))}
      {isAdmin ? (
        <Nav.Link as={NavLink} to="/admin" onClick={closeNav}>
          {t("nav.admin")}
        </Nav.Link>
      ) : null}
    </>
  ) : (
    <Nav.Link as={NavLink} to={setupHref} className="app-nav__setup-link" onClick={closeNav}>
      {t("nav.completeSetup")}
    </Nav.Link>
  );

  return (
    <>
      <Navbar
        expand="lg"
        className="app-navbar sticky-top"
        expanded={isPwaMode ? undefined : navExpanded}
        onToggle={isPwaMode ? undefined : setNavExpanded}
      >
        <div className="container-fluid container-lg">
          <Navbar.Brand as={Link} to="/" className="app-brand">
            <span className="app-brand__mark" aria-hidden="true">R</span>
            <span className="app-brand__lockup">
              <span className="app-brand__text">{t("common.appName")}</span>
              <span className="app-brand__tagline">{t("common.appTagline")}</span>
            </span>
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="main-nav" />
          <Navbar.Collapse id="main-nav">
            <Nav className="me-auto app-nav d-none d-lg-flex">{primaryNavLinks}</Nav>

            {!isPwaMode ? (
              <Nav className="app-nav app-nav--mobile d-lg-none" aria-label={t("nav.mainNavigation")}>
                {primaryNavLinks}
              </Nav>
            ) : null}

            <div className="d-flex align-items-center gap-2 py-2 py-lg-0 app-navbar__tools">
              <ThemeToggle variant="navbar" />
              <LanguageSwitcher variant="navbar" />

              <Dropdown align="end" className="user-dropdown">
                <Dropdown.Toggle variant="link" className="user-dropdown__toggle text-decoration-none">
                  <span className="user-dropdown__avatar">{displayName.charAt(0).toUpperCase()}</span>
                  <span className="d-none d-md-inline user-dropdown__name">{displayName}</span>
                </Dropdown.Toggle>
                <Dropdown.Menu className="user-dropdown__menu">
                  <Dropdown.Header className="user-dropdown__header">
                    <div className="fw-semibold">{user?.fullName ?? t("common.researcher")}</div>
                    <div className="user-dropdown__email">{user?.email ?? user?.phoneNumber}</div>
                    {isAdmin ? (
                      <div className="user-dropdown__role text-muted">{t("nav.adminAndResearcher")}</div>
                    ) : null}
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
                  {isAdmin ? (
                    <Dropdown.Item as={Link} to="/admin">
                      {t("nav.admin")}
                    </Dropdown.Item>
                  ) : null}
                  <Dropdown.Item as={Link} to="/how-it-works">
                    {t("nav.howItWorks")}
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/profile?tab=consent">
                    {t("nav.consent")}
                  </Dropdown.Item>
                  <Dropdown.Item
                    onClick={() => {
                      startTourForCurrentPage();
                    }}
                  >
                    {t("coachmarks.replay")}
                  </Dropdown.Item>
                  <Dropdown.Item
                    onClick={() => {
                      resetTours();
                      startTourForCurrentPage();
                    }}
                  >
                    {t("coachmarks.replayAll")}
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

      <main className={`app-main${isPwaMode ? " app-main--with-bottom-nav" : ""}`}>
        <div className="container-fluid container-lg">
          <SetupBanner />
          <PwaInstallBanner />
          <Outlet />
        </div>
      </main>

      {isPwaMode ? <MobileBottomNav /> : null}
    </>
  );
}
