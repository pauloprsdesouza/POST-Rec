import { useEffect } from "react";

import { Alert } from "react-bootstrap";

import { useTranslation } from "react-i18next";

import { Link, useParams } from "react-router-dom";



import { RecommendationViewer } from "@/features/runs/components/RecommendationViewer";

import { RunProgressPanel } from "@/features/runs/components/RunProgressPanel";

import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

import { OutcomeBadge } from "@/shared/ui/OutcomeBadge";

import { useAuth } from "@/features/auth/context/AuthContext";

import { useRuns } from "@/features/runs/context/RunsContext";

import { useRunDetail } from "@/features/runs/hooks/useRunDetail";

import { formatRunDateTime, formatRunTopics } from "@/features/runs/utils/runs";



export function RunDetailPage() {

  const { t, i18n } = useTranslation();

  const { runId } = useParams<{ runId: string }>();

  const { accessToken, sessionId, setSelectedRunId } = useAuth();

  const { updateRun } = useRuns();



  const {

    run,

    events,

    recommendations,

    refinementRecommendations,

    sources,

    error,

    loading,

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



  if (!runId || !accessToken) {

    return null;

  }



  if (loading) {

    return <LoadingSpinner label={t("common.loadingRun")} />;

  }



  if (error && !run) {

    return (

      <div className="page-shell">

        <Alert variant="danger">{error}</Alert>

        <Link to="/runs" className="btn btn-outline-primary">

          {t("runs.backToRuns")}

        </Link>

      </div>

    );

  }



  if (!run) {

    return (

      <div className="page-shell">

        <Alert variant="warning">{t("common.runNotFound")}</Alert>

        <Link to="/runs" className="btn btn-outline-primary">

          {t("runs.backToRuns")}

        </Link>

      </div>

    );

  }



  const isReady = outcome === "ready";



  return (

    <div className="page-shell run-detail">

      <header className="run-detail__header">

        <Link to="/runs" className="run-detail__back">

          {t("runs.backToRuns")}

        </Link>

        <div className="run-detail__headline">

          <OutcomeBadge outcome={outcome ?? "in_progress"} />

          {run.mode ? (
            <span className="run-detail__mode">{t(`newRun.runMode.${run.mode}.label`)}</span>
          ) : null}

          <time className="run-detail__date" dateTime={run.created_at ?? undefined}>

            {formatRunDateTime(run.created_at, i18n.language)}

          </time>

        </div>

        <h1 className="run-detail__title">{formatRunTopics(run, t("common.noTopics"), 200)}</h1>

      </header>



      {isReady ? (

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

          error={error}

        />

      ) : (

        <>

          <RunProgressPanel
            run={run}
            events={events}
            live={!usingFallbackPoll}
          />

          {outcome === "incomplete" ? (

            <Alert variant="warning" className="mt-3">

              {t("runs.completedWithoutIdeas")}

            </Alert>

          ) : null}

          {outcome === "failed" && run.error_message ? (

            <Alert variant="danger" className="mt-3">

              {run.error_message}

            </Alert>

          ) : null}

        </>

      )}

    </div>

  );

}


