import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  formatRelativeRunTime,
  formatRunDateTime,
  formatRunTopics,
  getRunDisplayProgress,
  getRunOutcome,
  type RunOutcome,
} from "@/features/runs/utils/runs";
import type { RecommendationRun } from "@/shared/types/api";
import { isBlindRun } from "@/features/experiments/utils/blindRun";

interface RunListCardProps {
  run: RecommendationRun;
  recommendationCount?: number;
  showSearchMeta?: boolean;
}

function StatusPill({ outcome }: { outcome: RunOutcome }) {
  const { t } = useTranslation();
  return (
    <span className={`run-card__status run-card__status--${outcome}`}>
      {t(`status.${outcome}`)}
    </span>
  );
}

function IdeaCountBadge({ count }: { count: number }) {
  return (
    <span className="run-card__ideas-badge" aria-hidden>
      <svg className="run-card__ideas-icon" viewBox="0 0 24 24" fill="none">
        <path
          d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2Z" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      {count}
    </span>
  );
}

export function RunListCard({ run, recommendationCount, showSearchMeta = false }: RunListCardProps) {
  const { t, i18n } = useTranslation();
  const runId = String(run.id);
  const count = recommendationCount ?? run.recommendation_count ?? 0;
  const outcome = getRunOutcome({ ...run, recommendation_count: count });
  const isReady = outcome === "ready";
  const isReviewed = outcome === "reviewed";
  const isActive = outcome === "in_progress";
  const displayProgress = getRunDisplayProgress(run);
  const blind = isBlindRun(run);
  const topics = (run.topics ?? []).filter(Boolean);
  const displayTopics = topics.slice(0, 3);
  const absoluteDate = formatRunDateTime(run.created_at, i18n.language);
  const relativeDate = formatRelativeRunTime(run.created_at, i18n.language);

  const cardClass = [
    "run-card",
    `run-card--${outcome}`,
    isReady ? "run-card--ready" : "",
    isActive ? "run-card--active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const actionLabel = isReady
    ? t("runs.reviewAndRate")
    : isReviewed
      ? t("runs.viewIdeas")
      : isActive
        ? t("runs.trackProgress")
        : outcome === "incomplete"
          ? t("runs.noIdeasGenerated")
          : t("common.viewDetails");

  return (
    <Link to={`/runs/${runId}`} className={cardClass}>
      <div className="run-card__main">
        <div className="run-card__top">
          <div className="run-card__meta">
            <StatusPill outcome={outcome} />
            {!blind && run.mode ? (
              <span className="run-card__mode">{t(`newRun.runMode.${run.mode}.label`)}</span>
            ) : null}
          </div>
          <time className="run-card__date" dateTime={run.created_at ?? undefined} title={absoluteDate}>
            {relativeDate || absoluteDate}
          </time>
        </div>

        <h3 className="run-card__title">{formatRunTopics(run, t("common.noTopics"), 100)}</h3>

        {showSearchMeta && run.search_snippet ? (
          <p className="run-card__search-snippet">{run.search_snippet}</p>
        ) : null}
        {showSearchMeta && (run.search_match_count ?? 0) > 0 ? (
          <p className="run-card__search-matches">
            {t("runs.searchMatchCount", { count: run.search_match_count })}
          </p>
        ) : null}

        {displayTopics.length > 0 ? (
          <ul className="run-card__topics" aria-label={t("runs.topicsLabel")}>
            {displayTopics.map((topic) => (
              <li key={topic} className="run-card__topic">
                {topic}
              </li>
            ))}
            {topics.length > displayTopics.length ? (
              <li className="run-card__topic run-card__topic--more">
                +{topics.length - displayTopics.length}
              </li>
            ) : null}
          </ul>
        ) : null}

        {isActive ? (
          <div className="run-card__progress">
            <div className="run-card__progress-bar">
              <div className="run-card__progress-fill" style={{ width: `${displayProgress}%` }} />
            </div>
            <span className="run-card__progress-label">{displayProgress}%</span>
          </div>
        ) : null}

        <div className="run-card__footer">
          <div className="run-card__footer-left">
            {isReady ? (
              <>
                <IdeaCountBadge count={count} />
                <span className="run-card__feedback-hint">{t("runs.rateIdeasHint")}</span>
              </>
            ) : isActive ? (
              <span className="run-card__status-hint">{t("runs.generatingHint")}</span>
            ) : null}
          </div>
          <span className={`run-card__action ${isReady ? "run-card__action--primary" : ""}`}>
            {actionLabel}
            <span className="run-card__arrow" aria-hidden>
              →
            </span>
          </span>
        </div>
      </div>
    </Link>
  );
}
