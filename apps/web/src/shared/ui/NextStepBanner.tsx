import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { PromoBanner } from "@/shared/ui/PromoBanner";

interface NextStepBannerProps {
  title: string;
  description: string;
  ctaLabel: string;
  ctaTo: string;
}

export function NextStepBanner({ title, description, ctaLabel, ctaTo }: NextStepBannerProps) {
  const { t } = useTranslation();

  return (
    <PromoBanner
      variant="step"
      role="status"
      icon="✓"
      title={title}
      description={description}
      actions={
        <Link to={ctaTo} className="btn btn-primary promo-banner__cta">
          {ctaLabel}
        </Link>
      }
      footnote={t("conversion.nextStepFootnote")}
    />
  );
}
