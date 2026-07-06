import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Recommendation, RecommendationRun, SourceDocument } from "@/shared/types/api";
import { isBlindRun } from "@/features/experiments/utils/blindRun";

import { IdeaCarousel } from "./IdeaCarousel";
import { RatingCelebration } from "./RatingCelebration";
import { RecommendationDetail } from "./RecommendationDetail";
import { RefinementPanel } from "./RefinementPanel";
import { SessionQuickFeedback } from "./SessionQuickFeedback";
import { SourceCatalog } from "./EvidenceList";
import { RunUsagePanel } from "./RunUsagePanel";
import { InlineAlert } from "@/shared/ui/InlineAlert";

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
  onFeedbackChange?: (ratedCount: number, total: number) => void;
}

function buildInitialRatings(recommendations: Recommendation[]): Record<string, number> {
  const ratings: Record<string, number> = {};
  for (const recommendation of recommendations) {
    const score = recommendation.user_feedback?.relevance_score;
    if (typeof score === "number") {
      ratings[recommendation.id] = score;
    }
  }
  return ratings;
}

function findNextIndex(
  recommendations: Recommendation[],
  skipIds: Set<string>,
  ratedIds: Set<string>,
  from: number,
): number {
  for (let i = from; i < recommendations.length; i += 1) {
    const id = recommendations[i].id;
    if (!ratedIds.has(id) && !skipIds.has(id)) {
      return i;
    }
  }
  for (let i = 0; i < from; i += 1) {
    const id = recommendations[i].id;
    if (!ratedIds.has(id) && !skipIds.has(id)) {
      return i;
    }
  }
  return -1;
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
  onFeedbackChange,
  error,
}: RecommendationViewerProps) {
  const { t } = useTranslation();
  const [ratings, setRatings] = useState<Record<string, number>>(() => buildInitialRatings(recommendations));
  const [celebration, setCelebration] = useState<"first" | "all" | null>(null);

  useEffect(() => {
    const initialRatings = buildInitialRatings(recommendations);
    setRatings(initialRatings);
    const ratedCount = Object.keys(initialRatings).length;
    if (ratedCount > 0) {
      onFeedbackChange?.(ratedCount, recommendations.length);
    }
  }, [onFeedbackChange, recommendations]);

  const handleRated = useCallback(
    (recommendationId: string, rating: number, isFirstRating: boolean) => {
      setRatings((prev) => {
        const next = { ...prev, [recommendationId]: rating };
        const nextCount = Object.keys(next).length;
        const total = recommendations.length;

        if (isFirstRating && nextCount === 1) {
          setCelebration("first");
        } else if (nextCount >= total && total > 0) {
          setCelebration("all");
        }

        onFeedbackChange?.(nextCount, recommendations.length);
        return next;
      });
    },
    [onFeedbackChange, recommendations.length],
  );

  const jumpToUnrated = useCallback(() => {
    const ratedIds = new Set(Object.keys(ratings));
    const nextIdx = findNextIndex(recommendations, new Set(), ratedIds, 0);
    if (nextIdx >= 0) {
      onActiveIndexChange(nextIdx);
    }
  }, [onActiveIndexChange, ratings, recommendations]);

  if (error) {
    return <InlineAlert variant="danger">{error}</InlineAlert>;
  }

  if (!recommendations.length && !refinementRecommendations.length) {
    return <p className="evidence-empty">{t("runs.noRecommendations")}</p>;
  }

  const active = recommendations[activeIndex];
  const blind = isBlindRun(run);
  const ratedIds = new Set(Object.keys(ratings));
  const ratedCount = ratedIds.size;
  const showSessionFeedback = ratedCount > 0;
  const remaining = Math.max(recommendations.length - ratedCount, 0);

  const celebrationMessage =
    celebration === "first"
      ? t("ideas.celebrationFirst", { remaining: remaining > 0 ? remaining : recommendations.length - 1 })
      : celebration === "all"
        ? t("ideas.celebrationAll")
        : "";

  return (
    <div className="idea-viewer">
      <RatingCelebration
        kind={celebration}
        message={celebrationMessage}
        onDismiss={() => setCelebration(null)}
      />

      {recommendations.length ? (
        <div data-coach="coach-run-carousel">
          <IdeaCarousel
            items={recommendations}
            activeIndex={activeIndex}
            ratedIds={ratedIds}
            skippedIds={new Set()}
            ratedCount={ratedCount}
            onSelect={onActiveIndexChange}
            onJumpToUnrated={ratedCount < recommendations.length ? jumpToUnrated : undefined}
          />
        </div>
      ) : null}

      {!blind ? <RunUsagePanel run={run} /> : null}

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
          initialRating={ratings[active.id] ?? null}
          onRated={handleRated}
        />
      ) : null}

      <RefinementPanel items={refinementRecommendations} />

      {showSessionFeedback ? (
        <aside className="feedback-footer">
          <p className="feedback-footer__title">{t("survey.quickPrompt")}</p>
          <SessionQuickFeedback runId={runId} visible compact />
        </aside>
      ) : null}

      {sources.length > 0 ? (
        <details className="idea-sources-all" data-coach="coach-run-sources">
          <summary>{t("runs.allSources", { count: sources.length })}</summary>
          <SourceCatalog sources={sources} />
        </details>
      ) : null}
    </div>
  );
}
