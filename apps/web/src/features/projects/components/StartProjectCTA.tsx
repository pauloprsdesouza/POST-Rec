import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { isRoadmapEligible } from "@/features/projects/utils/roadmapEligibility";
import type { WouldUse } from "@/features/runs/components/QuickFeedbackPanel";
import { projectService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import { getPwaMode } from "@/shared/pwa/detect";
import { InlineAlert } from "@/shared/ui/InlineAlert";

interface StartProjectCTAProps {
  token: string;
  recommendationId: string;
  rating: number | null;
  wouldUse: WouldUse;
  decision?: string | null;
  locale?: string;
  onEligibleChange?: (eligible: boolean) => void;
}

export function StartProjectCTA({
  token,
  recommendationId,
  rating,
  wouldUse,
  decision,
  locale: localeProp,
  onEligibleChange,
}: StartProjectCTAProps) {
  const { t, i18n } = useTranslation();
  const locale = localeProp ?? i18n.language;
  const navigate = useNavigate();
  const sectionRef = useRef<HTMLElement>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [loadingLookup, setLoadingLookup] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCommitted = isRoadmapEligible(rating, wouldUse, decision);

  useEffect(() => {
    onEligibleChange?.(isCommitted);
  }, [isCommitted, onEligibleChange]);

  useEffect(() => {
    if (!token || !isCommitted) {
      setLoadingLookup(false);
      return;
    }

    let active = true;
    setLoadingLookup(true);
    void (async () => {
      try {
        const existing = await projectService.getProjectByRecommendation(token, recommendationId);
        if (active && existing) {
          setProjectId(existing.id);
        }
      } catch {
        // ignore lookup errors
      } finally {
        if (active) {
          setLoadingLookup(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [token, recommendationId, isCommitted]);

  useEffect(() => {
    if (!isCommitted || loadingLookup) {
      return;
    }

    const isMobilePwa = getPwaMode() === "standalone" && window.innerWidth < 992;
    if (!isMobilePwa) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [isCommitted, loadingLookup, projectId]);

  const openProject = useCallback(
    (id: string) => {
      navigate(`/projects/${id}`);
    },
    [navigate],
  );

  const handleStart = async () => {
    if (projectId) {
      openProject(projectId);
      return;
    }

    setCreating(true);
    setError(null);
    try {
      const project = await projectService.createProject(token, recommendationId, locale);
      setProjectId(project.id);
      openProject(project.id);
    } catch (err) {
      setError(getErrorMessage(err, t("projects.createError")));
    } finally {
      setCreating(false);
    }
  };

  if (!isCommitted) {
    return null;
  }

  if (loadingLookup) {
    return (
      <section
        ref={sectionRef}
        className="start-project-cta start-project-cta--loading"
        aria-busy="true"
      >
        <div className="start-project-cta__skeleton" />
      </section>
    );
  }

  const buttonLabel = creating
    ? t("projects.creating")
    : projectId
      ? t("projects.openRoadmap")
      : t("projects.startRoadmap");

  return (
    <section
      ref={sectionRef}
      className="start-project-cta start-project-cta--eligible"
      aria-label={t("projects.ctaLabel")}
      data-coach="coach-run-roadmap"
    >
      <div className={`start-project-cta__card${projectId ? " start-project-cta__card--existing" : ""}`}>
        <div className="start-project-cta__layout">
          <div className="start-project-cta__copy">
            <h3 className="start-project-cta__title">
              {projectId ? t("projects.ctaExistingTitle") : t("projects.ctaTitle")}
            </h3>
            <p className="start-project-cta__body">{t("projects.ctaBody")}</p>
          </div>

          <div className="start-project-cta__actions">
            <button
              type="button"
              className="btn btn-primary start-project-cta__button"
              disabled={creating}
              onClick={() => void handleStart()}
            >
              {buttonLabel}
            </button>
          </div>
        </div>
      </div>
      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
    </section>
  );
}
