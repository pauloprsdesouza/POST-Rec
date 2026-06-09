import { useCallback, useEffect } from "react";

import { useTranslation } from "react-i18next";

import { Link, useParams } from "react-router-dom";

import { RecommendationViewer } from "@/features/runs/components/RecommendationViewer";

import { RunProgressPanel } from "@/features/runs/components/RunProgressPanel";

import { RunDetailSkeleton } from "@/features/runs/components/RunDetailSkeleton";

import { OutcomeBadge } from "@/shared/ui/OutcomeBadge";

import { InlineAlert } from "@/shared/ui/InlineAlert";

import { isBlindRun } from "@/features/experiments/utils/blindRun";
import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";

import { useRuns } from "@/features/runs/context/RunsContext";

import { useRunDetail } from "@/features/runs/hooks/useRunDetail";

import { RunManageActions } from "@/features/runs/components/RunManageActions";
import { formatRunDateTime, formatRunTopics } from "@/features/runs/utils/runs";

export function RunDetailPage() {
  const { t, i18n } = useTranslation();

  const { runId } = useParams<{ runId: string }>();

  const { accessToken, user, sessionId, setSessionId, setSelectedRunId } = useAuth();

  const { updateRun, refreshRuns } = useRuns();

  const {
    run,
    events,
    recommendations,
    refinementRecommendations,
    sources,
    error,
    loadingRun,
    loadingIdeas,
    outcome,
    activeIndex,
    setActiveIndex,
    usingFallbackPoll,
  } = useRunDetail({
    token: accessToken ?? "",
    runId: runId ?? "",
    onRunUpdate: updateRun,
  });

  useEffect(() => {
    if (runId) {
      setSelectedRunId(runId);
    }
  }, [runId, setSelectedRunId]);

  useEffect(() => {
    if (!accessToken || !user?.userId || sessionId) {
      return;
    }
    if (outcome !== "ready" && outcome !== "reviewed") {
      return;
    }

    void (async () => {
      const session = await sessionService.createSession(accessToken, user.userId);
      setSessionId(session.session_id);
    })();
  }, [accessToken, outcome, sessionId, setSessionId, user?.userId]);

  const handleFeedbackChange = useCallback(
    (ratedCount: number, total: number) => {
      if (!run) {
        return;
      }
      const feedbackComplete = total > 0 && ratedCount >= total;
      updateRun({
        ...run,
        feedback_count: ratedCount,
        feedback_complete: feedbackComplete,
      });
      if (feedbackComplete) {
        void refreshRuns();
      }
    },
    [refreshRuns, run, updateRun],
  );

  if (!runId || !accessToken) {
    return null;
  }

  if (loadingRun && !run) {
    return <RunDetailSkeleton variant="full" />;
  }

  if (error && !run) {
    return (
      <div className="page-shell">
        <InlineAlert variant="danger">{error}</InlineAlert>
        <Link to="/runs" className="btn btn-outline-primary">
          {t("runs.backToRuns")}
        </Link>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="page-shell">
        <InlineAlert variant="warning">{t("common.runNotFound")}</InlineAlert>
        <Link to="/runs" className="btn btn-outline-primary">
          {t("runs.backToRuns")}
        </Link>
      </div>
    );
  }

  const showIdeas = outcome === "ready" || outcome === "reviewed";
  const blind = isBlindRun(run);
  const loadingIdeasOnly = showIdeas && loadingIdeas && recommendations.length === 0;

  return (
    <div className="page-shell run-detail">
      <div className="page-stack page-stack--tight">
        <header className="run-detail__header">
        <Link to="/runs" className="run-detail__back">
          {t("runs.backToRuns")}
        </Link>

        <div className="run-detail__headline">
          <OutcomeBadge outcome={outcome ?? "in_progress"} />

          {!blind && run.mode ? (
            <span className="run-detail__mode">{t(`newRun.runMode.${run.mode}.label`)}</span>
          ) : null}

          <time className="run-detail__date" dateTime={run.created_at ?? undefined}>
            {formatRunDateTime(run.created_at, i18n.language)}
          </time>
        </div>

        <h1 className="run-detail__title">{formatRunTopics(run, t("common.noTopics"), 200)}</h1>
        </header>

        <RunManageActions
          token={accessToken}
          run={run}
          onRunUpdated={updateRun}
          onRunsChanged={refreshRuns}
        />

        {loadingIdeasOnly ? (
          <RunDetailSkeleton variant="ideas" />
        ) : showIdeas ? (
          <RecommendationViewer
          token={accessToken}
          runId={runId}
          sessionId={sessionId}
          run={run}
          recommendations={recommendations}
          refinementRecommendations={refinementRecommendations}
          sources={sources}
          activeIndex={activeIndex}
          onActiveIndexChange={setActiveIndex}
          onFeedbackChange={handleFeedbackChange}
          error={error}
        />
        ) : (
          <>
            <RunProgressPanel run={run} events={events} live={!usingFallbackPoll} />

            {outcome === "incomplete" ? (
              <InlineAlert variant="warning">
                {t("runs.completedWithoutIdeas")}
              </InlineAlert>
            ) : null}

            {outcome === "failed" && run.error_message ? (
              <InlineAlert variant="danger">{run.error_message}</InlineAlert>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
