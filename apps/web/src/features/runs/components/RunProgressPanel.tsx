import { useEffect, useMemo, useState } from "react";

import { useTranslation } from "react-i18next";

import type { RecommendationRun, RunEvent } from "@/shared/types/api";

import {
  RUN_PIPELINE_STAGES,
  formatRunElapsed,
  getRunDisplayProgress,
  getRunOutcome,
  getRunPipelineStageIndex,
} from "@/features/runs/utils/runs";

import { formatEstimatedCost } from "@/features/runs/utils/formatCost";

import { filterUserFacingEvents } from "@/features/runs/utils/runLog";

import { RunProgressBar } from "./RunProgressBar";
import { Panel } from "@/shared/ui/Panel";
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
  const stepLabel = t(`status.${stepKey}`, { defaultValue: humanizeStatus(stepKey) });
  const stepDescription = t(`statusDescriptions.${stepKey}`, {
    defaultValue: t("statusDescriptions.default", { step: stepLabel }),
  });
  const isActive = outcome === "in_progress";
  const displayProgress = getRunDisplayProgress(run);
  const costFormatted = formatEstimatedCost(run.estimated_cost_usd ?? 0, i18n.language);
  const pipelineIndex = getRunPipelineStageIndex(run.current_step ?? run.status);
  const pipelineStep =
    pipelineIndex >= 0 ? pipelineIndex + 1 : null;
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (!isActive) {
      return;
    }
    const timer = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [isActive]);

  const elapsed = formatRunElapsed(run.started_at, i18n.language, nowMs);

  return (
    <Panel className="run-progress">
      {isActive ? (
        <p className="run-progress__encourage">{t("progress.encourage")}</p>
      ) : null}
      {isActive ? (
        <div className="run-progress__meta">
          {pipelineStep ? (
            <span className="run-progress__meta-item">
              {t("progress.stageOf", {
                current: pipelineStep,
                total: RUN_PIPELINE_STAGES.length,
              })}
            </span>
          ) : null}
          {elapsed ? (
            <span className="run-progress__meta-item">
              {t("progress.elapsed", { time: elapsed })}
            </span>
          ) : null}
        </div>
      ) : null}
      <p className="run-progress__step">
        <strong className="run-progress__step-name">{stepLabel}</strong>
        {" — "}
        {stepDescription}
      </p>

      <RunProgressBar
        value={displayProgress}
        indeterminate={isActive && run.status === "searching_papers" && displayProgress < 32}
        tone={outcome === "failed" ? "danger" : outcome === "ready" ? "success" : "default"}
        label={t("progress.progressLabel")}
      />
      {!isActive ? (
        <div className="run-progress__stats">
          <div className="run-progress__stat">
            <span className="run-progress__stat-label">{t("progress.progressLabel")}</span>
            <span className="run-progress__stat-value">{displayProgress}%</span>
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
        <details className="run-progress__log mt-3" open={false}>
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
    </Panel>
  );
}
