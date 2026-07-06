import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ProjectListCard } from "@/features/projects/components/ProjectListCard";
import { ProjectsEmptyHero } from "@/features/projects/components/ProjectsEmptyHero";
import { useAuth } from "@/features/auth/context/AuthContext";
import { projectService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { ProjectListItem } from "@/shared/types/api";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";

export function ProjectsPage() {
  const { t } = useTranslation();
  const { accessToken } = useAuth();
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let active = true;
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const items = await projectService.listProjects(accessToken);
        if (active) {
          setProjects(items);
        }
      } catch (err) {
        if (active) {
          setError(getErrorMessage(err, t("projects.loadError")));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [accessToken, t]);

  return (
    <PageShell pageClass="projects-page" width="list">
      <PageHeader title={t("projects.pageTitle")} />

      {loading ? <LoadingSpinner label={t("projects.loading")} /> : null}
      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

      {!loading && !error && projects.length === 0 ? <ProjectsEmptyHero /> : null}

      {!loading && projects.length > 0 ? (
        <ul className="projects-list">
          {projects.map((project) => (
            <ProjectListCard key={project.id} project={project} />
          ))}
        </ul>
      ) : null}
    </PageShell>
  );
}
