import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { OnboardingProgress } from "@/shared/ui/OnboardingProgress";

export function SetupBanner() {
  const { t } = useTranslation();
  const { consentDone, profileDone } = useAuth();

  if (consentDone && profileDone) {
    return null;
  }

  const step = !consentDone ? "consent" : "profile";
  const message = step === "consent" ? t("setup.consentMessage") : t("setup.profileMessage");
  const actionTo = step === "consent" ? "/consent" : "/profile?tab=research";
  const ctaLabel = step === "consent" ? t("setup.reviewConsent") : t("setup.completeProfile");

  return (
    <aside className="setup-banner-v2" aria-labelledby="setup-banner-heading">
      <div className="setup-banner-v2__inner">
        <OnboardingProgress />
        <div className="setup-banner-v2__row">
          <div>
            <span className="setup-banner-v2__badge">{t("setup.timeEstimate")}</span>
            <p id="setup-banner-heading" className="setup-banner-v2__message">
              {message}
            </p>
          </div>
          <Link to={actionTo} className="btn btn-primary setup-banner-v2__cta">
            {ctaLabel} →
          </Link>
        </div>
      </div>
    </aside>
  );
}
