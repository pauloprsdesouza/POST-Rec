import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { PromoBanner } from "@/shared/ui/PromoBanner";

interface RunsReadyBannerProps {
  count: number;
  firstRunId?: string;
}

export function RunsReadyBanner({ count, firstRunId }: RunsReadyBannerProps) {
  const { t } = useTranslation();

  if (count <= 0) {
    return null;
  }

  return (
    <PromoBanner
      id="runs-ready-banner-title"
      variant="success"
      title={t("runs.readyBannerTitle", { count })}
      actions={
        firstRunId ? (
          <Link to={`/runs/${firstRunId}`} className="btn btn-primary promo-banner__cta">
            {t("runs.reviewFirst")}
          </Link>
        ) : null
      }
    />
  );
}
