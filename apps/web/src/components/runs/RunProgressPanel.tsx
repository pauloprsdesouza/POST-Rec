import { useMemo } from "react";

import { ProgressBar } from "react-bootstrap";

import { useTranslation } from "react-i18next";

import type { RecommendationRun, RunEvent } from "../../types/api";

import { getRunOutcome } from "../../utils/runs";

import { formatEstimatedCost } from "../../utils/formatCost";

import { filterUserFacingEvents } from "../../utils/runLog";

interface RunProgressPanelProps {
  run: RecommendationRun;
  events: RunEvent[];
  live?: boolean;
}

function humanizeStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function RunProgressPanel({ run, events, live = true }: RunProgressPanelProps) {
  const { t, i18n } = useTranslation();
  const outcome = getRunOutcome(run);
  const isTerminal = outcome !== "in_progress";

  const visibleEvents = useMemo(() => {
    const meaningful = filterUserFacingEvents(events).filter((event) => event.message?.trim());
    return meaningful.slice(-12).reverse();
  }, [events]);

  const warningCount = visibleEvents.filter((event) => event.level === "warning").length;

  const stepKey = run.current_step ?? run.status;
  const step = t(`status.${stepKey}`, { defaultValue: humanizeStatus(stepKey) });
  const isActive = outcome === "in_progress";
  const costFormatted = formatEstimatedCost(run.estimated_cost_usd ?? 0, i18n.language);

  return (
    <div className="surface-card run-progress">
      <p className="run-progress__step">{t("progress.step", { step })}</p>

      <ProgressBar
        now={run.progress}
        label={`${run.progress}%`}
        className="run-progress__bar"
        variant={outcome === "failed" ? "danger" : outcome === "ready" ? "success" : undefined}
      />

      {!isActive ? (
        <div className="run-progress__stats">
          <div className="run-progress__stat">
            <span className="run-progress__stat-label">{t("progress.progressLabel")}</span>
            <span className="run-progress__stat-value">{run.progress}%</span>
          </div>
          <div className="run-progress__stat">
            <span className="run-progress__stat-label">{t("progress.estCost")}</span>
            <span className="run-progress__stat-value">{costFormatted}</span>
          </div>
        </div>
      ) : null}

      {!isTerminal && live ? (
        <p className="run-progress__hint">{t("progress.liveUpdates")}</p>
      ) : null}
      {!isTerminal && !live ? (
        <p className="run-progress__hint">{t("progress.updating")}</p>
      ) : null}

      {visibleEvents.length > 0 ? (
        <details className="run-progress__log mt-3" open={!isTerminal}>
          <summary>
            {t("progress.activityLog")}
            {warningCount > 0 && !isTerminal ? (
              <span className="run-progress__log-badge">{warningCount}</span>
            ) : null}
          </summary>
          <ul className="run-progress__log-list">
            {visibleEvents.map((event, index) => (
              <li
                key={`${event.created_at}-${index}`}
                className={`run-progress__log-item run-progress__log-item--${event.level ?? "info"}`}
              >
                <span className="run-progress__log-time">
                  {event.created_at
                    ? new Intl.DateTimeFormat(i18n.language, { timeStyle: "short" }).format(
                        new Date(event.created_at),
                      )
                    : ""}
                </span>
                <span className="run-progress__log-message">{event.message}</span>
              </li>
            ))}
          </ul>
          {!isTerminal ? (
            <p className="run-progress__log-note">{t("progress.recoverableHint")}</p>
          ) : null}
        </details>
      ) : null}
    </div>
  );
}
