import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function ProjectsEmptyHero() {
  const { t } = useTranslation();

  return (
    <section className="projects-empty-hero" aria-labelledby="projects-empty-title">
      <h2 id="projects-empty-title" className="projects-empty-hero__title">
        {t("projects.emptyTitle")}
      </h2>
      <p className="projects-empty-hero__subtitle">{t("projects.emptyBody")}</p>
      <Link to="/runs" className="btn btn-primary projects-empty-hero__cta">
        {t("projects.emptyAction")}
      </Link>
    </section>
  );
}
