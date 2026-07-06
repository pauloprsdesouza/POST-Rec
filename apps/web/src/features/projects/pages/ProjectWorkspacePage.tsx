import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { PhaseTimeline } from "@/features/projects/components/PhaseTimeline";
import { ProjectCompletionBanner } from "@/features/projects/components/ProjectCompletionBanner";
import { ProjectProgressHeader } from "@/features/projects/components/ProjectProgressHeader";
import { ProjectSourcePanel } from "@/features/projects/components/ProjectSourcePanel";
import { ProjectWorkspaceSkeleton } from "@/features/projects/components/ProjectWorkspaceSkeleton";
import { TaskCard } from "@/features/projects/components/TaskCard";
import {
  countProjectProgress,
  resolveActivePhaseId,
  sortTasks,
} from "@/features/projects/utils/projectUtils";
import { useAuth } from "@/features/auth/context/AuthContext";
import { projectService, runService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import { PaperRefProvider } from "@/features/runs/components/PaperRefContext";
import { buildPaperRefIndex, normalizePaperId } from "@/features/runs/utils/paperRefs";
import type { ProjectTaskStatus, Recommendation, ResearchProject, SourceDocument } from "@/shared/types/api";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { PageShell } from "@/shared/ui/PageShell";

export function ProjectWorkspacePage() {
  const { t } = useTranslation();
  const { projectId } = useParams<{ projectId: string }>();
  const { accessToken } = useAuth();
  const [project, setProject] = useState<ResearchProject | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activePhaseId, setActivePhaseId] = useState<string | null>(null);
  const [justCompletedTaskId, setJustCompletedTaskId] = useState<string | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [sourcePanelOpen, setSourcePanelOpen] = useState(false);
  const [sourceFocusField, setSourceFocusField] = useState<string | null>(null);

  const loadProject = useCallback(async () => {
    if (!accessToken || !projectId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await projectService.getProject(accessToken, projectId);
      setProject(data);
      setActivePhaseId((current) => resolveActivePhaseId(data, current));
    } catch (err) {
      setError(getErrorMessage(err, t("projects.loadError")));
    } finally {
      setLoading(false);
    }
  }, [accessToken, projectId, t]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  useEffect(() => {
    if (!accessToken || !project) {
      return;
    }

    let active = true;
    setSourceLoading(true);

    void (async () => {
      try {
        const [recommendations, sourceDocuments] = await Promise.all([
          runService.getRecommendations(accessToken, project.run_id),
          runService.getSourceDocuments(accessToken, project.run_id),
        ]);
        if (!active) {
          return;
        }
        setRecommendation(
          recommendations.find((item) => item.id === project.recommendation_id) ?? null,
        );
        setSources(sourceDocuments);
      } catch {
        if (active) {
          setRecommendation(null);
          setSources([]);
        }
      } finally {
        if (active) {
          setSourceLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [accessToken, project]);

  useEffect(() => {
    if (!justCompletedTaskId) {
      return;
    }
    const timer = window.setTimeout(() => setJustCompletedTaskId(null), 900);
    return () => window.clearTimeout(timer);
  }, [justCompletedTaskId]);

  const paperRefIndex = useMemo(
    () => (recommendation ? buildPaperRefIndex(recommendation, sources) : new Map()),
    [recommendation, sources],
  );

  const navigateToPaper = useCallback((paperId: string) => {
    const normalized = normalizePaperId(paperId);
    setSourcePanelOpen(true);
    window.requestAnimationFrame(() => {
      document.getElementById(`paper-ref-${normalized}`)?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    });
  }, []);

  const navigateToField = useCallback((field: string) => {
    setSourceFocusField(field);
    setSourcePanelOpen(true);
  }, []);

  const progress = useMemo(() => (project ? countProjectProgress(project) : null), [project]);

  const activePhase = useMemo(() => {
    if (!project || !activePhaseId) {
      return null;
    }
    return project.phases.find((phase) => phase.id === activePhaseId) ?? null;
  }, [project, activePhaseId]);

  const visibleTasks = useMemo(() => {
    if (!activePhase) {
      return [];
    }
    const tasks = sortTasks(activePhase.tasks);
    if (showCompleted) {
      return tasks;
    }
    return tasks.filter((task) => task.status !== "done" && task.status !== "skipped");
  }, [activePhase, showCompleted]);

  const hiddenCompletedCount = useMemo(() => {
    if (!activePhase || showCompleted) {
      return 0;
    }
    return activePhase.tasks.filter((task) => task.status === "done" || task.status === "skipped").length;
  }, [activePhase, showCompleted]);

  const updateTaskStatus = async (taskId: string, status: ProjectTaskStatus) => {
    if (!accessToken || !projectId) {
      return;
    }
    const previousStatus = project?.phases
      .flatMap((phase) => phase.tasks)
      .find((task) => task.id === taskId)?.status;

    setUpdatingTaskId(taskId);
    setError(null);
    try {
      await projectService.updateTask(accessToken, projectId, taskId, { status });
      const refreshed = await projectService.getProject(accessToken, projectId);
      setProject(refreshed);
      setActivePhaseId(resolveActivePhaseId(refreshed, activePhaseId));

      if (status === "done" && previousStatus !== "done") {
        setJustCompletedTaskId(taskId);
      }
    } catch (err) {
      setError(getErrorMessage(err, t("projects.updateError")));
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleNotesChange = async (taskId: string, notes: string) => {
    if (!accessToken || !projectId) {
      return;
    }
    setUpdatingTaskId(taskId);
    try {
      await projectService.updateTask(accessToken, projectId, taskId, { user_notes: notes });
      setProject((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          phases: current.phases.map((phase) => ({
            ...phase,
            tasks: phase.tasks.map((task) =>
              task.id === taskId ? { ...task, user_notes: notes } : task,
            ),
          })),
        };
      });
    } catch (err) {
      setError(getErrorMessage(err, t("projects.updateError")));
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleExport = async () => {
    if (!accessToken || !projectId) {
      return;
    }
    setExporting(true);
    setError(null);
    try {
      const markdown = await projectService.exportMarkdown(accessToken, projectId);
      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `research-project-${projectId}.md`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err, t("projects.exportError")));
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <PageShell pageClass="project-workspace-page" width="wide">
        <ProjectWorkspaceSkeleton />
      </PageShell>
    );
  }

  if (error && !project) {
    return (
      <PageShell pageClass="project-workspace-page">
        <InlineAlert variant="danger">{error}</InlineAlert>
        <Link to="/projects" className="btn btn-outline-secondary btn-sm mt-3">
          {t("projects.backToProjects")}
        </Link>
      </PageShell>
    );
  }

  if (!project) {
    return null;
  }

  const isComplete = progress != null && progress.total > 0 && progress.done >= progress.total;

  const workspaceBody = (
    <>
      <ProjectProgressHeader
        project={project}
        isComplete={isComplete}
        exporting={exporting}
        onExport={isComplete ? undefined : () => void handleExport()}
      />

      {recommendation ? (
        <ProjectSourcePanel
          recommendation={recommendation}
          runId={project.run_id}
          open={sourcePanelOpen}
          onOpenChange={setSourcePanelOpen}
          focusField={sourceFocusField}
          onFocusHandled={() => setSourceFocusField(null)}
        />
      ) : sourceLoading ? (
        <p className="project-source-panel__loading">{t("projects.source.loading")}</p>
      ) : null}

      {isComplete ? (
        <ProjectCompletionBanner onExport={() => void handleExport()} exporting={exporting} />
      ) : null}

      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

      <div className="project-workspace">
        <aside className="project-workspace__sidebar">
          <PhaseTimeline
            project={project}
            activePhaseId={activePhaseId}
            onSelectPhase={(phaseId) => {
              setActivePhaseId(phaseId);
            }}
          />
        </aside>

        <section className="project-workspace__main" aria-labelledby="project-phase-heading">
          {activePhase ? (
            <>
              <div className="project-workspace__phase-header">
                <h2 id="project-phase-heading" className="project-workspace__phase-title">
                  {activePhase.title}
                </h2>
                {activePhase.description ? (
                  <p className="project-workspace__phase-description">{activePhase.description}</p>
                ) : null}
              </div>

              {hiddenCompletedCount > 0 || showCompleted ? (
                <div className="project-workspace__task-toolbar">
                  <button
                    type="button"
                    className={`btn btn-sm project-workspace__filter-btn${
                      showCompleted
                        ? " project-workspace__filter-btn--active"
                        : " btn-outline-secondary"
                    }`}
                    aria-pressed={showCompleted}
                    onClick={() => setShowCompleted((value) => !value)}
                  >
                    {showCompleted
                      ? t("projects.hideCompleted")
                      : t("projects.showCompletedCount", { count: hiddenCompletedCount })}
                  </button>
                </div>
              ) : null}

              {visibleTasks.length === 0 ? (
                <div className="project-workspace__empty-phase">
                  <p>{t("projects.phaseComplete")}</p>
                  {hiddenCompletedCount > 0 ? (
                    <button
                      type="button"
                      className="btn btn-link btn-sm"
                      onClick={() => setShowCompleted(true)}
                    >
                      {t("projects.showCompletedCount", { count: hiddenCompletedCount })}
                    </button>
                  ) : null}
                </div>
              ) : (
                <div className="project-workspace__tasks">
                  {visibleTasks.map((task, index) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      taskNumber={task.order_index + 1 || index + 1}
                      justCompleted={justCompletedTaskId === task.id}
                      defaultExpanded={task.status === "in_progress"}
                      updating={updatingTaskId === task.id}
                      onStatusChange={(taskId, status) => void updateTaskStatus(taskId, status)}
                      onNotesChange={(taskId, notes) => void handleNotesChange(taskId, notes)}
                      onNavigateToField={recommendation ? navigateToField : undefined}
                    />
                  ))}
                </div>
              )}
            </>
          ) : (
            <p>{t("projects.noPhase")}</p>
          )}
        </section>
      </div>
    </>
  );

  return (
    <PageShell pageClass="project-workspace-page" width="wide">
      {recommendation ? (
        <PaperRefProvider index={paperRefIndex} onNavigateToPaper={navigateToPaper}>
          {workspaceBody}
        </PaperRefProvider>
      ) : (
        workspaceBody
      )}
    </PageShell>
  );
}
