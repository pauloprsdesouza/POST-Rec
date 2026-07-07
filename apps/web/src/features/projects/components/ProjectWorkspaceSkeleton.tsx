import { useTranslation } from "react-i18next";

export function ProjectWorkspaceSkeleton() {
  const { t } = useTranslation();

  return (
    <div className="project-skeleton" aria-busy="true" aria-live="polite">
      <span className="visually-hidden">{t("projects.loading")}</span>
      <div className="project-skeleton__header" />
      <div className="project-skeleton__mobile">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="project-skeleton__phase-block">
            <div className="project-skeleton__phase" />
            <div className="project-skeleton__main">
              {Array.from({ length: 2 }).map((__, taskIndex) => (
                <div key={taskIndex} className="project-skeleton__task" />
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="project-skeleton__layout">
        <div className="project-skeleton__sidebar">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="project-skeleton__phase" />
          ))}
        </div>
        <div className="project-skeleton__main">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="project-skeleton__task" />
          ))}
        </div>
      </div>
    </div>
  );
}
