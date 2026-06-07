import { useState } from "react";

import { Alert } from "react-bootstrap";

import { Link, Navigate } from "react-router-dom";

import { useTranslation } from "react-i18next";



import { RunListCard } from "@/features/runs/components/RunListCard";

import { EmptyState } from "@/shared/ui/EmptyState";

import { PageHeader } from "@/shared/ui/PageHeader";

import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

import { useAuth } from "@/features/auth/context/AuthContext";

import { useRuns } from "@/features/runs/context/RunsContext";

import type { RecommendationRun } from "@/shared/types/api";

import { groupRuns } from "@/features/runs/utils/runs";



const SECTION_STORAGE_PREFIX = "postrec.runs.section.";



function readSectionOpen(sectionId: string, defaultOpen: boolean): boolean {

  try {

    const stored = sessionStorage.getItem(`${SECTION_STORAGE_PREFIX}${sectionId}`);

    if (stored === "true") {

      return true;

    }

    if (stored === "false") {

      return false;

    }

  } catch {

    // ignore

  }

  return defaultOpen;

}



function writeSectionOpen(sectionId: string, open: boolean): void {

  try {

    sessionStorage.setItem(`${SECTION_STORAGE_PREFIX}${sectionId}`, String(open));

  } catch {

    // ignore

  }

}



function CollapsibleRunSection({

  sectionId,

  title,

  runs,

  defaultOpen = true,

}: {

  sectionId: string;

  title: string;

  runs: RecommendationRun[];

  defaultOpen?: boolean;

}) {

  const [open, setOpen] = useState(() => readSectionOpen(sectionId, defaultOpen));



  if (!runs.length) {

    return null;

  }



  const toggle = () => {

    setOpen((value) => {

      const next = !value;

      writeSectionOpen(sectionId, next);

      return next;

    });

  };



  return (

    <section className={`run-section run-section--collapsible ${open ? "run-section--open" : ""}`}>

      <button

        type="button"

        className="run-section__toggle"

        aria-expanded={open}

        onClick={toggle}

      >

        <span className="run-section__heading">{title}</span>

        <span className="run-section__count">{runs.length}</span>

        <span className="run-section__chevron" aria-hidden>

          {open ? "−" : "+"}

        </span>

      </button>

      {open ? (

        <div className="run-section__list">

          {runs.map((run) => (

            <RunListCard key={run.id} run={run} recommendationCount={run.recommendation_count} />

          ))}

        </div>

      ) : null}

    </section>

  );

}



export function RunsPage() {

  const { t } = useTranslation();

  const { accessToken } = useAuth();

  const { runs, loaded, loading, error } = useRuns();



  if (!accessToken) {

    return null;

  }



  if (!loaded && loading) {

    return <LoadingSpinner label={t("common.loadingRuns")} />;

  }



  if (error && !runs.length) {

    return <Alert variant="danger">{error}</Alert>;

  }



  if (!runs.length) {

    return (

      <div className="page-shell">

        <PageHeader title={t("runs.title")} subtitle={t("runs.subtitleEmpty")} />

        <EmptyState

          title={t("runs.noRunsTitle")}

          description={t("runs.noRunsDescription")}

          action={

            <Link to="/runs/new" className="btn btn-primary btn-lg w-100 w-sm-auto">

              {t("runs.startRun")}

            </Link>

          }

        />

      </div>

    );

  }



  const { active, completed, other } = groupRuns(runs);



  return (

    <div className="page-shell">

      <PageHeader

        title={t("runs.title")}

        subtitle={t("runs.subtitleStats", {

          total: runs.length,

          active: active.length,

          completed: completed.length,

        })}

        action={

          <Link to="/runs/new" className="btn btn-primary">

            {t("common.newRun")}

          </Link>

        }

      />



      {error ? <Alert variant="danger">{error}</Alert> : null}



      <CollapsibleRunSection

        sectionId="in_progress"

        title={t("runs.sectionInProgress")}

        runs={active}

        defaultOpen

      />

      <CollapsibleRunSection

        sectionId="ready"

        title={t("runs.sectionReady")}

        runs={completed}

        defaultOpen

      />



      {other.length > 0 ? (

        <CollapsibleRunSection

          sectionId="other"

          title={t("runs.sectionOtherCount", { count: other.length })}

          runs={other}

          defaultOpen={false}

        />

      ) : null}

    </div>

  );

}



export function RecommendationsRedirect() {

  const { selectedRunId } = useAuth();



  if (selectedRunId) {

    return <Navigate to={`/runs/${selectedRunId}`} replace />;

  }

  return <Navigate to="/runs" replace />;

}


