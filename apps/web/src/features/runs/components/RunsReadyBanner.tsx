import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

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
    <aside className="runs-ready-banner" aria-labelledby="runs-ready-banner-title">
      <div className="runs-ready-banner__content">
        <p id="runs-ready-banner-title" className="runs-ready-banner__title">
          {t("runs.readyBannerTitle", { count })}
        </p>
        <p className="runs-ready-banner__text">{t("runs.readyBannerText")}</p>
      </div>
      {firstRunId ? (
        <Link to={`/runs/${firstRunId}`} className="btn btn-primary runs-ready-banner__cta">
          {t("runs.reviewFirst")}
        </Link>
      ) : null}
    </aside>
  );
}
