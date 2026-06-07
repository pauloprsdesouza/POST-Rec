import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import { InlineAlert } from "@/shared/ui/InlineAlert";
interface SessionQuickFeedbackProps {
  runId: string;
  visible?: boolean;
  compact?: boolean;
}

export function SessionQuickFeedback({
  runId,
  visible = true,
  compact = false,
}: SessionQuickFeedbackProps) {
  const { t } = useTranslation();
  const { accessToken, user, sessionId } = useAuth();
  const [expectationMet, setExpectationMet] = useState<number | null>(null);
  const [wouldUseAgain, setWouldUseAgain] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (score: number, useAgain: boolean) => {
      if (!accessToken || !user || submitting || done) {
        return;
      }
      setSubmitting(true);
      setError(null);
      try {
        await sessionService.submitSurvey(accessToken, {
          session_id: sessionId,
          run_id: runId,
          user_id: user.userId,
          expectation_met_score: score,
          would_use_any_recommendation_in_real_paper: score >= 4 ? "yes" : score >= 3 ? "maybe" : "no",
          would_use_again: useAgain,
          would_recommend: useAgain,
        });
        setDone(true);
      } catch (err) {
        setError(getErrorMessage(err, t("survey.errorSubmit")));
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken, done, runId, sessionId, submitting, t, user],
  );

  const handleScore = (value: number) => {
    setExpectationMet(value);
    if (wouldUseAgain != null) {
      void submit(value, wouldUseAgain);
    }
  };

  const handleUseAgain = (value: boolean) => {
    setWouldUseAgain(value);
    if (expectationMet != null) {
      void submit(expectationMet, value);
    }
  };

  if (!visible) {
    return null;
  }

  if (done) {
    return (
      <div className={`session-quick-feedback session-quick-feedback--done ${compact ? "session-quick-feedback--compact" : ""}`}>
        <p className="session-quick-feedback__thanks">{t("survey.thankYouShort")}</p>
        <div className="session-quick-feedback__actions">
          <Link to="/runs/new" className="btn btn-primary btn-sm">
            {t("runs.completeBanner.newRun")}
          </Link>
          <Link to="/runs" className="btn btn-outline-secondary btn-sm">
            {t("survey.backToRuns")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={`session-quick-feedback ${compact ? "session-quick-feedback--compact" : ""}`}>
      {!compact ? (
        <p className="session-quick-feedback__prompt">{t("survey.quickPrompt")}</p>
      ) : null}
      <p className="session-quick-feedback__hint">{t("survey.autoSaveHint")}</p>

      <div className="session-quick-feedback__row">
        <span className="session-quick-feedback__label">{t("survey.quickSatisfaction")}</span>
        <div className="quick-rating__stars" role="group">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              className={`quick-rating__star ${expectationMet === value ? "quick-rating__star--selected" : ""} ${expectationMet != null && expectationMet >= value ? "quick-rating__star--filled" : ""}`}
              disabled={submitting}
              aria-label={t("ideas.rateValue", { value })}
              aria-pressed={expectationMet === value}
              onClick={() => handleScore(value)}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      <div className="session-quick-feedback__row">
        <span className="session-quick-feedback__label">{t("survey.quickUseAgain")}</span>
        <div className="quick-rating__chips">
          <button
            type="button"
            className={`quick-rating__chip ${wouldUseAgain === true ? "quick-rating__chip--active" : ""}`}
            disabled={submitting}
            aria-pressed={wouldUseAgain === true}
            onClick={() => handleUseAgain(true)}
          >
            {t("common.yes")}
          </button>
          <button
            type="button"
            className={`quick-rating__chip ${wouldUseAgain === false ? "quick-rating__chip--active" : ""}`}
            disabled={submitting}
            aria-pressed={wouldUseAgain === false}
            onClick={() => handleUseAgain(false)}
          >
            {t("common.no")}
          </button>
        </div>
      </div>

      {submitting ? <p className="session-quick-feedback__saving">{t("survey.submitting")}</p> : null}
      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
    </div>  );
}
