import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface RunCompleteBannerProps {
  ideaCount: number;
  ratedCount: number;
}

function ThumbUpIcon() {
  return (
    <svg className="run-complete-banner__svg" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M7 10v10H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h3Zm2-1 4.5-4.2a1.5 1.5 0 0 1 2.5 1.1V10h4.3a2 2 0 0 1 1.95 2.45l-1.5 6A2 2 0 0 1 18.8 20H9V9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ThumbDownIcon() {
  return (
    <svg className="run-complete-banner__svg" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M17 14V4h3a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-3Zm-2 1-4.5 4.2a1.5 1.5 0 0 1-2.5-1.1V14H3.7a2 2 0 0 1-1.95-2.45l1.5-6A2 2 0 0 1 5.2 4H15v11Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function RunCompleteBanner({ ideaCount, ratedCount }: RunCompleteBannerProps) {
  const { t } = useTranslation();
  const allRated = ratedCount >= ideaCount;
  const remaining = Math.max(ideaCount - ratedCount, 0);

  return (
    <aside className={`run-complete-banner ${allRated ? "run-complete-banner--all-rated" : ""}`}>
      <div className="run-complete-banner__content">
        <div className="run-complete-banner__title">
          {allRated ? t("runs.completeBanner.allRatedTitle") : t("runs.completeBanner.title")}
        </div>
        <p className="run-complete-banner__text">
          {allRated
            ? t("runs.completeBanner.allRatedText")
            : t("runs.completeBanner.textProgress", { remaining })}
        </p>
        {!allRated ? (
          <div className="run-complete-banner__feedback-hint">
            <span className="run-complete-banner__thumb run-complete-banner__thumb--up">
              <ThumbUpIcon />
            </span>
            <span className="run-complete-banner__thumb run-complete-banner__thumb--down">
              <ThumbDownIcon />
            </span>
            <span className="run-complete-banner__hint-label">{t("runs.completeBanner.thumbHint")}</span>
          </div>
        ) : null}
      </div>
      {allRated ? (
        <div className="run-complete-banner__secondary">
          <Link to="/runs/new" className="btn btn-primary btn-sm">
            {t("runs.completeBanner.newRun")}
          </Link>
        </div>
      ) : null}
    </aside>
  );
}
