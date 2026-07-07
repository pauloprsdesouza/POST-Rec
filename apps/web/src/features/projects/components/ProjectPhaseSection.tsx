import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { TaskCard } from "@/features/projects/components/TaskCard";
import {
  countPhaseTasks,
  getPhaseVisualState,
  sortTasks,
} from "@/features/projects/utils/projectUtils";
import type { ProjectPhase, ProjectTaskStatus } from "@/shared/types/api";

interface ProjectPhaseSectionProps {
  phase: ProjectPhase;
  phaseIndex: number;
  currentPhaseId?: string | null;
  justCompletedTaskId: string | null;
  updatingTaskId: string | null;
  onStatusChange: (taskId: string, status: ProjectTaskStatus) => void;
  onNotesChange: (taskId: string, notes: string) => void;
  onNavigateToField?: (field: string) => void;
  headingId?: string;
  withCoachPhase?: boolean;
  withCoachTasks?: boolean;
}

export function ProjectPhaseSection({
  phase,
  phaseIndex,
  currentPhaseId,
  justCompletedTaskId,
  updatingTaskId,
  onStatusChange,
  onNotesChange,
  onNavigateToField,
  headingId,
  withCoachPhase = false,
  withCoachTasks = false,
}: ProjectPhaseSectionProps) {
  const { t } = useTranslation();
  const [showCompleted, setShowCompleted] = useState(false);
  const phaseState = getPhaseVisualState(phase, currentPhaseId);
  const stats = countPhaseTasks(phase);

  const visibleTasks = useMemo(() => {
    const tasks = sortTasks(phase.tasks);
    if (showCompleted) {
      return tasks;
    }
    return tasks.filter((task) => task.status !== "done" && task.status !== "skipped");
  }, [phase.tasks, showCompleted]);

  const hiddenCompletedCount = useMemo(() => {
    if (showCompleted) {
      return 0;
    }
    return phase.tasks.filter((task) => task.status === "done" || task.status === "skipped").length;
  }, [phase.tasks, showCompleted]);

  const resolvedHeadingId = headingId ?? `project-phase-${phase.id}-heading`;

  return (
    <section
      id={`project-phase-${phase.id}`}
      className={[
        "project-phase-section",
        `project-phase-section--${phaseState}`,
        phaseState === "current" ? "project-phase-section--current" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-labelledby={resolvedHeadingId}
      data-coach={withCoachPhase ? "coach-projects-phases" : undefined}
    >
      <header className="project-phase-section__header">
        <div className="project-phase-section__heading-row">
          <span className="project-phase-section__marker" aria-hidden>
            {phaseState === "done" ? "✓" : phaseIndex + 1}
          </span>
          <div className="project-phase-section__heading-copy">
            <h2 id={resolvedHeadingId} className="project-phase-section__title">
              {phase.title}
            </h2>
            {phase.description ? (
              <p className="project-phase-section__description">{phase.description}</p>
            ) : null}
          </div>
        </div>
        {stats.total > 0 ? (
          <p className="project-phase-section__meta">
            {t("projects.phaseProgressCount", { done: stats.done, total: stats.total })}
          </p>
        ) : null}
      </header>

      <div className="project-phase-section__body">
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
          <div
            className="project-workspace__tasks project-phase-section__tasks"
            data-coach={withCoachTasks ? "coach-projects-tasks" : undefined}
          >
            {visibleTasks.map((task, index) => (
              <TaskCard
                key={task.id}
                task={task}
                taskNumber={task.order_index + 1 || index + 1}
                justCompleted={justCompletedTaskId === task.id}
                defaultExpanded={task.status === "in_progress"}
                updating={updatingTaskId === task.id}
                onStatusChange={onStatusChange}
                onNotesChange={onNotesChange}
                onNavigateToField={onNavigateToField}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
