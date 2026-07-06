import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import { ProjectLinkedFields } from "@/features/projects/components/ProjectLinkedReferences";
import { PaperRefText } from "@/features/runs/components/PaperRefText";
import type { ProjectTask, ProjectTaskStatus } from "@/shared/types/api";

interface TaskCardProps {
  task: ProjectTask;
  taskNumber: number;
  updating: boolean;
  justCompleted?: boolean;
  defaultExpanded?: boolean;
  onStatusChange: (taskId: string, status: ProjectTaskStatus) => void;
  onNotesChange: (taskId: string, notes: string) => void;
  onNavigateToField?: (field: string) => void;
}

function StatusIcon({ status }: { status: ProjectTaskStatus }) {
  if (status === "done") {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
        <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5.5 9.2 7.8 11.5 12.5 6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }
  if (status === "in_progress") {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
        <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="9" cy="9" r="3" fill="currentColor" />
      </svg>
    );
  }
  if (status === "skipped") {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
        <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 2" />
      </svg>
    );
  }
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function TaskCard({
  task,
  taskNumber,
  updating,
  justCompleted = false,
  defaultExpanded = false,
  onStatusChange,
  onNotesChange,
  onNavigateToField,
}: TaskCardProps) {
  const { t } = useTranslation();
  const bodyId = useId();
  const [notes, setNotes] = useState(task.user_notes ?? "");
  const [expanded, setExpanded] = useState(defaultExpanded || task.status === "in_progress");

  useEffect(() => {
    setNotes(task.user_notes ?? "");
  }, [task.user_notes, task.id]);

  const isDone = task.status === "done";
  const isSkipped = task.status === "skipped";

  const toggleDone = () => {
    onStatusChange(task.id, isDone ? "todo" : "done");
  };

  return (
    <article
      id={`project-task-${task.id}`}
      className={[
        "task-card",
        `task-card--${task.status}`,
        justCompleted ? "task-card--just-completed" : "",
        expanded ? "task-card--expanded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="task-card__header">
        <button
          type="button"
          className={`task-card__check${isDone ? " task-card__check--done" : ""}`}
          disabled={updating || isSkipped}
          aria-label={isDone ? t("projects.actions.markTodo") : t("projects.actions.markDone")}
          onClick={toggleDone}
        >
          <StatusIcon status={task.status} />
        </button>

        <div className="task-card__content">
          <button
            type="button"
            className="task-card__summary"
            aria-expanded={expanded}
            aria-controls={bodyId}
            onClick={() => setExpanded((value) => !value)}
          >
            <span className="task-card__title-row">
              <span className="task-card__number">{taskNumber}</span>
              <span className={`task-card__title${isDone ? " task-card__title--done" : ""}`}>
                <PaperRefText text={task.title} />
              </span>
            </span>
          </button>

          <div className="task-card__quick-actions">
            {task.status === "todo" ? (
              <button
                type="button"
                className="btn btn-outline-primary btn-sm"
                disabled={updating}
                onClick={() => onStatusChange(task.id, "in_progress")}
              >
                {t("projects.actions.start")}
              </button>
            ) : null}
            {!isDone && !isSkipped ? (
              <button
                type="button"
                className="btn btn-link btn-sm task-card__skip"
                disabled={updating}
                onClick={() => onStatusChange(task.id, "skipped")}
              >
                {t("projects.actions.skip")}
              </button>
            ) : null}
            {isSkipped ? (
              <button
                type="button"
                className="btn btn-link btn-sm"
                disabled={updating}
                onClick={() => onStatusChange(task.id, "todo")}
              >
                {t("projects.actions.restore")}
              </button>
            ) : null}
          </div>
        </div>
      </div>

      {expanded ? (
        <div id={bodyId} className="task-card__body">
          {task.description ? (
            <p className="task-card__description">
              <PaperRefText text={task.description} />
            </p>
          ) : null}
          {task.guidance ? (
            <div className="task-card__guidance">
              <span className="task-card__guidance-label">{t("projects.whyItMatters")}</span>
              <p>
                <PaperRefText text={task.guidance} />
              </p>
            </div>
          ) : null}
          {task.checklist && task.checklist.length > 0 ? (
            <ul className="task-card__checklist" aria-label={t("projects.checklistLabel")}>
              {task.checklist.map((item) => (
                <li key={item}>
                  <PaperRefText text={item} />
                </li>
              ))}
            </ul>
          ) : null}
          {task.linked_fields && task.linked_fields.length > 0 && onNavigateToField ? (
            <ProjectLinkedFields fields={task.linked_fields} onNavigateToField={onNavigateToField} />
          ) : null}
          <label className="task-card__notes-label">
            {t("projects.notes")}
            <textarea
              className="form-control task-card__notes"
              rows={2}
              value={notes}
              disabled={updating}
              placeholder={t("projects.notesPlaceholder")}
              onChange={(event) => setNotes(event.target.value)}
              onBlur={() => {
                if (notes !== (task.user_notes ?? "")) {
                  onNotesChange(task.id, notes);
                }
              }}
            />
          </label>
        </div>
      ) : null}
    </article>
  );
}
