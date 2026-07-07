import { useTranslation } from "react-i18next";

interface ProjectCompletionBannerProps {
  onExport: () => void;
  exporting: boolean;
}

export function ProjectCompletionBanner({ onExport, exporting }: ProjectCompletionBannerProps) {
  const { t } = useTranslation();

  return (
    <section className="project-completion" aria-labelledby="project-completion-title">
      <h2 id="project-completion-title" className="project-completion__title">
        {t("projects.completion.title")}
      </h2>
      <button type="button" className="btn btn-success btn-sm" disabled={exporting} onClick={onExport}>
        {exporting ? t("projects.exporting") : t("projects.completion.export")}
      </button>
    </section>
  );
}
