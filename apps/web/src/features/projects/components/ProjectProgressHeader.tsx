import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { ProgressRing } from "@/features/projects/components/ProgressRing";
import { countProjectProgress } from "@/features/projects/utils/projectUtils";
import type { ResearchProject } from "@/shared/types/api";

interface ProjectProgressHeaderProps {
  project: ResearchProject;
  isComplete?: boolean;
  exporting?: boolean;
  onExport?: () => void;
}

export function ProjectProgressHeader({
  project,
  isComplete = false,
  exporting = false,
  onExport,
}: ProjectProgressHeaderProps) {
  const { t } = useTranslation();
  const stats = countProjectProgress(project);

  return (
    <header className="page-stack__block project-header">
      <Link to="/projects" className="project-header__back">
        ← {t("projects.backToProjects")}
      </Link>

      <div className="project-header__hero">
        <h1 className="project-header__title">{project.title}</h1>

        <div className="project-header__visual">
          <ProgressRing
            value={stats.pct}
            size={72}
            stroke={6}
            variant={isComplete ? "success" : "primary"}
            sublabel={t("projects.progressRingLabel")}
          />
          {onExport ? (
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm project-header__export"
              disabled={exporting}
              onClick={onExport}
            >
              {exporting ? t("projects.exporting") : t("projects.exportMarkdown")}
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
