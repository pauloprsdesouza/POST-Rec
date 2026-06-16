import { useState } from "react";
import { useTranslation } from "react-i18next";

import { runService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { Recommendation, SourceDocument } from "@/shared/types/api";
import { EvidenceList } from "./EvidenceList";
import { QuickFeedbackPanel, type WouldUse } from "./QuickFeedbackPanel";
import { ScoreBar } from "./ScoreBar";
import { SotaVerificationPanel } from "./SotaVerificationPanel";
type IdeaSection = "summary" | "method" | "sources";

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
  onSkip?: () => void;
}

export function RecommendationDetail({
  recommendation,
  index,
  total,
  runId,
  sessionId,
  token,
  sources = [],
  initialRating = null,
  onRated,
  onSkip,
}: RecommendationDetailProps) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<IdeaSection>("summary");
  const [savedRating, setSavedRating] = useState<number | null>(initialRating);
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
    <article className="idea-detail">
      <div className="idea-detail__meta">
        <span className="idea-detail__counter">
          {t("ideas.countOfTotal", { current: index, total })}
        </span>
        {scoreLabel != null ? (
          <span className="idea-detail__score">{t("ideas.score", { value: scoreLabel })}</span>
        ) : null}
        <span className="idea-detail__chip">{confidence}</span>
        <span className="idea-detail__chip">{t("ideas.sourcesCount", { count: sourceCount })}</span>
      </div>

      <h2 className="idea-detail__title">{recommendation.title}</h2>
      {recommendation.technique_name ? (
        <p className="idea-detail__technique">{recommendation.technique_name}</p>
      ) : null}

      <div data-coach="coach-run-rating">
      <QuickFeedbackPanel
        rating={savedRating}
        wouldUse={wouldUse}
        submitting={submitting}
        message={message}
        error={error}
        onThumbUp={() => applyRating(4)}
        onThumbDown={() => applyRating(2)}
        onSkip={onSkip}
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

      <nav className="idea-tabs" aria-label={t("ideas.sectionNav")}>
        {(
          [
            ["summary", t("ideas.summary")],
            ["method", t("ideas.methodPlan")],
            ["sources", t("ideas.evidence", { count: sourceCount })],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`idea-tabs__btn ${activeSection === key ? "idea-tabs__btn--active" : ""}`}
            aria-selected={activeSection === key}
            onClick={() => setActiveSection(key)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="idea-tab-panel">
        {activeSection === "summary" ? (
          <>
            <Section label={t("ideas.researchGap")} value={recommendation.research_gap} />
            <Section label={t("ideas.researchQuestion")} value={recommendation.research_question} />
            <Section label={t("ideas.hypothesis")} value={recommendation.hypothesis} />
            <Section label={t("ideas.contribution")} value={recommendation.expected_contribution} />
            <Section label={t("ideas.relatedWork")} value={recommendation.related_work_summary} />
            <SotaVerificationPanel recommendation={recommendation} sources={sources} />
            {recommendation.scores ? (
              <div className="idea-scores">
                <p className="idea-scores__heading">{t("ideas.qualityScores")}</p>
                {Object.entries(recommendation.scores)
                  .filter(([name]) =>
                    ["relevance", "novelty", "evidence", "feasibility"].includes(name),
                  )
                  .map(([name, value]) => (
                    <ScoreBar
                      key={name}
                      label={t(`ideas.scoreNames.${name}`, {
                        defaultValue: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                      })}
                      value={value}
                    />
                  ))}
              </div>
            ) : null}
          </>
        ) : null}

        {activeSection === "method" ? (
          <>
            <Section label={t("ideas.proposedMethod")} value={recommendation.proposed_method} />
            <Section label={t("ideas.experimentalPlan")} value={recommendation.experimental_plan} />
            <ListSection label={t("ideas.datasets")} items={recommendation.datasets} />
            <ListSection label={t("ideas.metrics")} items={recommendation.evaluation_metrics} />
            <ListSection label={t("ideas.risks")} items={recommendation.risks} />
          </>
        ) : null}

        {activeSection === "sources" ? (
          <EvidenceList papers={recommendation.evidence_papers} />
        ) : null}
      </div>
    </article>
  );
}

function Section({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <p className="idea-block__text">{value}</p>
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
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
