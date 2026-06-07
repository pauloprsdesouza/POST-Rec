import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { EmptyIllustration } from "@/shared/ui/illustrations/EmptyIllustration";

export function RunsEmptyHero() {
  const { t } = useTranslation();

  const steps = [
    t("runs.emptyHeroStep1"),
    t("runs.emptyHeroStep2"),
    t("runs.emptyHeroStep3"),
  ];

  return (
    <section className="runs-empty-hero" aria-labelledby="runs-empty-title">
      <EmptyIllustration variant="runs" className="runs-empty-hero__art" />

      <div className="runs-empty-hero__content">
        <p className="runs-empty-hero__eyebrow">{t("runs.emptyHeroEyebrow")}</p>
        <h2 id="runs-empty-title" className="runs-empty-hero__title">
          {t("runs.emptyHeroTitle")}
        </h2>
        <p className="runs-empty-hero__subtitle">{t("runs.emptyHeroSubtitle")}</p>

        <ol className="runs-empty-hero__steps">
          {steps.map((step, index) => (
            <li key={step} className="runs-empty-hero__step">
              <span className="runs-empty-hero__step-num">{index + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>

        <div className="runs-empty-hero__actions">
          <Link to="/runs/new" className="btn btn-primary btn-lg runs-empty-hero__cta" data-coach="coach-runs-new-run">
            {t("runs.emptyHeroCta")}
          </Link>
          <Link to="/how-it-works" className="runs-empty-hero__link">
            {t("runs.emptyHeroLearnMore")}
          </Link>
        </div>
      </div>
    </section>
  );
}
