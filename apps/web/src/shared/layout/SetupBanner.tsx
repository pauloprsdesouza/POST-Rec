import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { OnboardingProgress } from "@/shared/ui/OnboardingProgress";
import { PromoBanner } from "@/shared/ui/PromoBanner";

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
    <PromoBanner
      id="setup-banner-heading"
      badge={t("setup.timeEstimate")}
      message={message}
      header={<OnboardingProgress />}
      actions={
        <Link to={actionTo} className="btn btn-primary promo-banner__cta">
          {ctaLabel} →
        </Link>
      }
    />
  );
}
