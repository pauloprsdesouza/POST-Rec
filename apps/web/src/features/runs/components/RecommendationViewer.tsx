import { useTranslation } from "react-i18next";

import { Alert } from "react-bootstrap";

import type { Recommendation, RecommendationRun, SourceDocument } from "@/shared/types/api";

import { IdeaCarousel } from "./IdeaCarousel";

import { RecommendationDetail } from "./RecommendationDetail";
import { RefinementPanel } from "./RefinementPanel";
import { SourceCatalog } from "./EvidenceList";
import { RunUsagePanel } from "./RunUsagePanel";



interface RecommendationViewerProps {

  token: string;

  runId: string;

  sessionId: string | null;

  run: RecommendationRun;

  recommendations: Recommendation[];

  refinementRecommendations?: Recommendation[];

  sources: SourceDocument[];

  activeIndex: number;

  onActiveIndexChange: (index: number) => void;

  error?: string | null;

}



export function RecommendationViewer({

  token,

  runId,

  sessionId,

  run,

  recommendations,

  refinementRecommendations = [],

  sources,

  activeIndex,

  onActiveIndexChange,

  error,

}: RecommendationViewerProps) {

  const { t } = useTranslation();



  if (error) {

    return <Alert variant="danger">{error}</Alert>;

  }



  if (!recommendations.length && !refinementRecommendations.length) {

    return <p className="text-secondary mb-0">{t("runs.noRecommendations")}</p>;

  }



  const active = recommendations[activeIndex];



  return (

    <div className="idea-viewer">

      <RunUsagePanel run={run} />

      {recommendations.length ? (
        <IdeaCarousel
          items={recommendations}
          activeIndex={activeIndex}
          onSelect={onActiveIndexChange}
        />
      ) : null}



      {active ? (

        <RecommendationDetail

          key={active.id}

          recommendation={active}

          index={activeIndex + 1}

          total={recommendations.length}

          runId={runId}

          sessionId={sessionId}

          token={token}

          sources={sources}

        />

      ) : null}

      <RefinementPanel items={refinementRecommendations} />



      {sources.length > 0 ? (

        <details className="idea-sources-all mt-4">

          <summary>{t("runs.allSources", { count: sources.length })}</summary>

          <div className="mt-2">

            <SourceCatalog sources={sources} />

          </div>

        </details>

      ) : null}

    </div>

  );

}


