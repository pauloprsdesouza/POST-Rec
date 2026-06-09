import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";

type StepId = "consent" | "profile" | "firstRun";

const STEPS: StepId[] = ["consent", "profile", "firstRun"];

function stepState(step: StepId, consentDone: boolean, profileDone: boolean): "done" | "current" | "upcoming" {
  if (step === "consent") {
    if (consentDone) return "done";
    return "current";
  }
  if (step === "profile") {
    if (profileDone) return "done";
    if (consentDone) return "current";
    return "upcoming";
  }
  if (profileDone) return "current";
  return "upcoming";
}

export function OnboardingProgress() {
  const { t } = useTranslation();
  const { consentDone, profileDone } = useAuth();

  if (consentDone && profileDone) {
    return null;
  }

  return (
    <nav className="onboarding-progress" aria-label={t("onboarding.progressLabel")}>
      <ol className="onboarding-progress__list">
        {STEPS.map((step, index) => {
          const state = stepState(step, consentDone, profileDone);

          return (
            <li
              key={step}
              className={`onboarding-progress__step onboarding-progress__step--${state}`}
            >
              <span className="onboarding-progress__marker" aria-hidden>
                {state === "done" ? "✓" : index + 1}
              </span>
              <span className="onboarding-progress__label">{t(`onboarding.steps.${step}`)}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
