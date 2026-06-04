import { Alert } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext";

export function SetupBanner() {
  const { t } = useTranslation();
  const { consentDone, profileDone } = useAuth();

  if (consentDone && profileDone) {
    return null;
  }

  const step = !consentDone ? "consent" : "profile";
  const message = step === "consent" ? t("setup.consentMessage") : t("setup.profileMessage");

  return (
    <Alert variant="warning" className="setup-banner mb-4">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2">
        <span>
          <strong>{t("setup.title")}</strong> {message}
        </span>
        <Link
          to={step === "consent" ? "/consent" : "/profile?tab=research"}
          className="btn btn-sm btn-warning"
        >
          {step === "consent" ? t("setup.reviewConsent") : t("setup.completeProfile")}
        </Link>
      </div>
    </Alert>
  );
}
