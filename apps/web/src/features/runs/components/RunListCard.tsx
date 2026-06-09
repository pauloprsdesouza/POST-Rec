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

function StatusPill({ outcome, run }: { outcome: RunOutcome; run: RecommendationRun }) {
  const { t } = useTranslation();
  const isActive = outcome === "in_progress";
  const stageKey = run.current_step ?? run.status;
  const label = isActive
    ? t(`status.${stageKey}`, { defaultValue: t("status.in_progress") })
    : t(`status.${outcome}`);

  return <span className={`run-card__status run-card__status--${outcome}`}>{label}</span>;
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
  const absoluteDate = formatRunDateTime(run.created_at, i18n.language);
  const relativeDate = formatRelativeRunTime(run.created_at, i18n.language);
  const title = formatRunTopics(run, t("common.noTopics"), 120);

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
    <li>
      <Link
        to={`/runs/${runId}`}
        className={`run-card run-card--${outcome}`}
        aria-label={`${actionLabel}: ${title}`}
      >
        <div className="run-card__body">
          <div className="run-card__content">
            <h3 className="run-card__title">{title}</h3>

            <div className="run-card__meta-row">
              <StatusPill outcome={outcome} run={run} />
              {!blind && run.mode ? (
                <span className="run-card__mode">{t(`newRun.runMode.${run.mode}.label`)}</span>
              ) : null}
              {isReady && count > 0 ? (
                <span className="run-card__ideas-count">{t("runs.ideasReady", { count })}</span>
              ) : null}
              <time className="run-card__date" dateTime={run.created_at ?? undefined} title={absoluteDate}>
                {relativeDate || absoluteDate}
              </time>
            </div>

            {showSearchMeta && run.search_snippet ? (
              <p className="run-card__search-snippet">{run.search_snippet}</p>
            ) : null}
            {showSearchMeta && (run.search_match_count ?? 0) > 0 ? (
              <p className="run-card__search-matches">
                {t("runs.searchMatchCount", { count: run.search_match_count })}
              </p>
            ) : null}

            {isActive ? (
              <div className="run-card__progress">
                <div className="run-card__progress-bar" role="presentation">
                  <div className="run-card__progress-fill" style={{ width: `${displayProgress}%` }} />
                </div>
                <span className="run-card__progress-label">{displayProgress}%</span>
              </div>
            ) : null}

            {isReady ? <p className="run-card__hint">{t("runs.rateIdeasHint")}</p> : null}
            {isActive ? (
              <p className="run-card__hint">
                {t(`statusDescriptions.${run.current_step ?? run.status}`, {
                  defaultValue: t("runs.generatingHint"),
                })}
              </p>
            ) : null}
          </div>

          <span className="run-card__cta">
            {actionLabel}
            <span className="run-card__arrow" aria-hidden>
              →
            </span>
          </span>
        </div>
      </Link>
    </li>
  );
}
