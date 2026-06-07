import { Link } from "react-router-dom";

import { useTranslation } from "react-i18next";



import { formatRunDateTime, formatRunTopics, getRunOutcome } from "@/features/runs/utils/runs";

import type { RecommendationRun } from "@/shared/types/api";

import { OutcomeBadge } from "@/shared/ui/OutcomeBadge";



interface RunListCardProps {

  run: RecommendationRun;

  recommendationCount?: number;

}



export function RunListCard({ run, recommendationCount }: RunListCardProps) {

  const { t, i18n } = useTranslation();

  const runId = String(run.id);

  const count = recommendationCount ?? run.recommendation_count ?? 0;

  const outcome = getRunOutcome({ ...run, recommendation_count: count });

  const isReady = outcome === "ready";

  const isActive = outcome === "in_progress";



  return (

    <Link to={`/runs/${runId}`} className="run-card">

      <div className="run-card__top">

        <OutcomeBadge outcome={outcome} />

        {run.mode ? (
          <span className="run-card__mode">{t(`newRun.runMode.${run.mode}.label`)}</span>
        ) : null}

        <time className="run-card__date" dateTime={run.created_at ?? undefined}>

          {formatRunDateTime(run.created_at, i18n.language)}

        </time>

      </div>

      <h3 className="run-card__title">{formatRunTopics(run, t("common.noTopics"), 120)}</h3>

      {isActive ? (

        <div className="run-card__progress">

          <div className="run-card__progress-bar">

            <div className="run-card__progress-fill" style={{ width: `${run.progress}%` }} />

          </div>

          <span className="run-card__progress-label">{run.progress}%</span>

        </div>

      ) : null}

      {isReady ? (

        <p className="run-card__cta">

          {t("runs.ideasReady", { count })} →

        </p>

      ) : isActive ? (

        <p className="run-card__cta">{t("runs.trackProgress")}</p>

      ) : outcome === "incomplete" ? (

        <p className="run-card__cta text-warning-emphasis">{t("runs.noIdeasGenerated")}</p>

      ) : (

        <p className="run-card__cta text-secondary">{t("common.viewDetails")}</p>

      )}

    </Link>

  );

}


