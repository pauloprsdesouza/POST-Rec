import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface NextStepBannerProps {
  title: string;
  description: string;
  ctaLabel: string;
  ctaTo: string;
}

export function NextStepBanner({ title, description, ctaLabel, ctaTo }: NextStepBannerProps) {
  const { t } = useTranslation();

  return (
    <div className="next-step-banner" role="status">
      <div className="next-step-banner__icon" aria-hidden>
        ✓
      </div>
      <div className="next-step-banner__body">
        <p className="next-step-banner__title">{title}</p>
        <p className="next-step-banner__desc">{description}</p>
      </div>
      <Link to={ctaTo} className="btn btn-primary next-step-banner__cta">
        {ctaLabel}
      </Link>
      <p className="next-step-banner__footnote">{t("conversion.nextStepFootnote")}</p>
    </div>
  );
}
