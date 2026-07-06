import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { runService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { Recommendation, SourceDocument } from "@/shared/types/api";
import { PaperRefProvider } from "./PaperRefContext";
import { PaperRefText } from "./PaperRefText";
import { EvidenceList } from "./EvidenceList";
import { QuickFeedbackPanel, type WouldUse } from "./QuickFeedbackPanel";
import { ScoreBar } from "./ScoreBar";
import { SotaVerificationPanel } from "./SotaVerificationPanel";
import { buildPaperRefIndex, normalizePaperId } from "@/features/runs/utils/paperRefs";

type IdeaTab = "about" | "summary" | "method" | "evidence";

interface RecommendationDetailProps {
  recommendation: Recommendation;
  index: number;
  total: number;
  runId: string;
  sessionId: string | null;
  token: string;
  sources?: SourceDocument[];
  initialRating?: number | null;
  onRated?: (recommendationId: string, rating: number, isFirstRating: boolean) => void;
}

export function RecommendationDetail({
  recommendation,
  runId,
  sessionId,
  token,
  sources = [],
  initialRating = null,
  onRated,
}: RecommendationDetailProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<IdeaTab>("about");
  const [savedRating, setSavedRating] = useState<number | null>(initialRating);

  useEffect(() => {
    setActiveTab("about");
    setSavedRating(initialRating);
  }, [recommendation.id, initialRating]);
  const [wouldUse, setWouldUse] = useState<WouldUse>("maybe");
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const scoreLabel =
    recommendation.final_score != null ? Math.round(recommendation.final_score) : null;
  const confidenceKey = (recommendation.confidence_level ?? "medium").toLowerCase();
  const confidence = t(`ideas.confidence.${confidenceKey}`, {
    defaultValue: confidenceKey.replace(/\b\w/g, (c) => c.toUpperCase()),
  });
  const sourceCount = recommendation.evidence_papers?.length ?? 0;
  const paperRefIndex = useMemo(
    () => buildPaperRefIndex(recommendation, sources),
    [recommendation, sources],
  );

  const navigateToPaper = useCallback((paperId: string) => {
    const normalized = normalizePaperId(paperId);
    setActiveTab("evidence");
    window.requestAnimationFrame(() => {
      document.getElementById(`paper-ref-${normalized}`)?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    });
  }, []);
  const qualityScores = recommendation.scores
    ? Object.entries(recommendation.scores).filter(([name]) =>
        ["relevance", "novelty", "evidence", "feasibility"].includes(name),
      )
    : [];

  const decisionFromRating = (rating: number) => {
    if (rating >= 4) return "approved";
    if (rating >= 3) return "save";
    if (rating === 2) return "needs_revision";
    return "rejected";
  };

  const wouldUseFromRating = (rating: number): WouldUse => {
    if (rating >= 4) return "yes";
    if (rating >= 3) return "maybe";
    return "no";
  };

  const submitRating = async (rating: number, useInPaper = wouldUse) => {
    const isFirstRating = savedRating == null;
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await runService.submitFeedback(token, recommendation.id, {
        session_id: sessionId,
        run_id: runId,
        relevance_score: rating,
        originality_score: rating,
        clarity_score: rating,
        feasibility_score: rating,
        trust_score: rating,
        usefulness_score: rating,
        would_use_in_real_paper: useInPaper,
        decision: decisionFromRating(rating),
        comment: comment.trim() || undefined,
      });
      setSavedRating(rating);
      setMessage(isFirstRating ? t("ideas.feedbackSavedNext") : t("ideas.feedbackSavedShort"));
      onRated?.(recommendation.id, rating, isFirstRating);
    } catch (err) {
      setError(getErrorMessage(err, t("ideas.feedbackError")));
    } finally {
      setSubmitting(false);
    }
  };

  const applyRating = (rating: number) => {
    const useInPaper = savedRating == null ? wouldUseFromRating(rating) : wouldUse;
    if (savedRating == null) {
      setWouldUse(useInPaper);
    }
    void submitRating(rating, useInPaper);
  };

  return (
    <PaperRefProvider index={paperRefIndex} onNavigateToPaper={navigateToPaper}>
      <article className="idea-detail" aria-labelledby={`idea-title-${recommendation.id}`}>
      <div className="idea-detail__meta">
        {scoreLabel != null ? (
          <span className="idea-detail__score" title={t("ideas.scoreHint")}>
            {t("ideas.score", { value: scoreLabel })}
          </span>
        ) : null}
        <span className="idea-detail__chip" title={t("ideas.confidenceHint")}>
          {confidence}
        </span>
        <span className="idea-detail__chip" title={t("ideas.sourcesHint")}>
          {t("ideas.sourcesCount", { count: sourceCount })}
        </span>
      </div>

      <h2 className="idea-detail__title" id={`idea-title-${recommendation.id}`}>
        {recommendation.title}
      </h2>
      {recommendation.technique_name ? (
        <p className="idea-detail__technique">{recommendation.technique_name}</p>
      ) : null}

      <div className="idea-detail__body">
        <nav className="idea-tabs" role="tablist" aria-label={t("ideas.sectionNav")}>
          {(
            [
              ["about", t("ideas.about")],
              ["summary", t("ideas.summary")],
              ["method", t("ideas.methodPlan")],
              ["evidence", t("ideas.evidence", { count: sourceCount })],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              role="tab"
              id={`idea-tab-${recommendation.id}-${tab}`}
              aria-selected={activeTab === tab}
              aria-controls={`idea-panel-${recommendation.id}-${tab}`}
              className={`idea-tabs__btn${activeTab === tab ? " idea-tabs__btn--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {label}
            </button>
          ))}
        </nav>

        {activeTab === "about" ? (
          <div
            role="tabpanel"
            id={`idea-panel-${recommendation.id}-about`}
            aria-labelledby={`idea-tab-${recommendation.id}-about`}
            className="idea-tab-panel"
          >
            <p className="idea-tab-panel__intro">{t("ideas.sectionAboutIntro")}</p>
            <Section label={t("ideas.researchGap")} value={recommendation.research_gap} />
            <Section label={t("ideas.researchQuestion")} value={recommendation.research_question} />
            <Section label={t("ideas.contribution")} value={recommendation.expected_contribution} />
            {qualityScores.length > 0 ? (
              <details className="idea-detail__scores">
                <summary>{t("ideas.qualityScores")}</summary>
                <div className="idea-scores">
                  {qualityScores.map(([name, value]) => (
                    <ScoreBar
                      key={name}
                      label={t(`ideas.scoreNames.${name}`, {
                        defaultValue: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                      })}
                      value={value}
                    />
                  ))}
                </div>
              </details>
            ) : null}
          </div>
        ) : null}

        {activeTab === "summary" ? (
          <div
            role="tabpanel"
            id={`idea-panel-${recommendation.id}-summary`}
            aria-labelledby={`idea-tab-${recommendation.id}-summary`}
            className="idea-tab-panel"
          >
            <p className="idea-tab-panel__intro">{t("ideas.sectionSummaryIntro")}</p>
            <Section label={t("ideas.hypothesis")} value={recommendation.hypothesis} />
            <Section label={t("ideas.relatedWork")} value={recommendation.related_work_summary} />
          </div>
        ) : null}

        {activeTab === "method" ? (
          <div
            role="tabpanel"
            id={`idea-panel-${recommendation.id}-method`}
            aria-labelledby={`idea-tab-${recommendation.id}-method`}
            className="idea-tab-panel"
          >
            <p className="idea-tab-panel__intro">{t("ideas.sectionMethodIntro")}</p>
            <Section label={t("ideas.proposedMethod")} value={recommendation.proposed_method} />
            <Section label={t("ideas.experimentalPlan")} value={recommendation.experimental_plan} />
            <ListSection label={t("ideas.datasets")} items={recommendation.datasets} />
            <ListSection label={t("ideas.metrics")} items={recommendation.evaluation_metrics} />
            <ListSection label={t("ideas.risks")} items={recommendation.risks} />
            <SotaVerificationPanel recommendation={recommendation} sources={sources} />
          </div>
        ) : null}

        {activeTab === "evidence" ? (
          <div
            role="tabpanel"
            id={`idea-panel-${recommendation.id}-evidence`}
            aria-labelledby={`idea-tab-${recommendation.id}-evidence`}
            className="idea-tab-panel"
          >
            <p className="idea-tab-panel__intro">{t("ideas.sectionEvidenceIntro")}</p>
            <EvidenceList papers={recommendation.evidence_papers} />
          </div>
        ) : null}
      </div>

      <div className="idea-detail__feedback-dock" data-coach="coach-run-rating">
        <p className="idea-detail__guide">{t("ideas.readGuide")}</p>
        <QuickFeedbackPanel
          rating={savedRating}
          wouldUse={wouldUse}
          submitting={submitting}
          message={message}
          error={error}
          onStarClick={applyRating}
          onWouldUseChange={(value) => {
            setWouldUse(value);
            if (savedRating != null) {
              void submitRating(savedRating, value);
            }
          }}
          comment={comment}
          onCommentChange={setComment}
          onCommentBlur={() => {
            if (savedRating != null && comment.trim()) {
              void submitRating(savedRating, wouldUse);
            }
          }}
        />
      </div>
      </article>
    </PaperRefProvider>
  );
}

function Section({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <p className="idea-block__text">
        <PaperRefText text={value} />
      </p>
    </div>
  );
}

function ListSection({ label, items }: { label: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <ul className="idea-block__list">
        {items.map((item) => (
          <li key={item}>
            <PaperRefText text={item} />
          </li>
        ))}
      </ul>
    </div>
  );
}
