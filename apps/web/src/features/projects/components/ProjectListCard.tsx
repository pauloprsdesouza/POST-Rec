import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import type { ProjectListItem } from "@/shared/types/api";

interface ProjectListCardProps {
  project: ProjectListItem;
}

export function ProjectListCard({ project }: ProjectListCardProps) {
  const { t } = useTranslation();
  const isComplete = project.status === "completed" || project.progress_pct >= 100;

  return (
    <li>
      <Link
        to={`/projects/${project.id}`}
        className={`project-card${isComplete ? " project-card--complete" : ""}`}
        aria-label={`${project.title}. ${project.progress_pct}% ${t("projects.overallProgress")}`}
      >
        <div className="project-card__layout">
          <div className="project-card__body">
            <h2 className="project-card__title">{project.title}</h2>
            <p className="project-card__meta">
              {isComplete
                ? t("projects.list.complete", { pct: project.progress_pct })
                : project.current_phase_title
                  ? t("projects.list.progress", {
                      pct: project.progress_pct,
                      phase: project.current_phase_title,
                    })
                  : t("projects.list.progressShort", { pct: project.progress_pct })}
            </p>
          </div>
          <span className="project-card__arrow" aria-hidden>
            →
          </span>
        </div>
      </Link>
    </li>
  );
}
