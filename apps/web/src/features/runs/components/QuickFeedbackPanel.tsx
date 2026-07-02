import { Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { InlineAlert } from "@/shared/ui/InlineAlert";
export type WouldUse = "yes" | "maybe" | "no";

function ThumbUpIcon() {
  return (
    <svg className="quick-feedback__icon" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M7 10v10H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h3Zm2-1 4.5-4.2a1.5 1.5 0 0 1 2.5 1.1V10h4.3a2 2 0 0 1 1.95 2.45l-1.5 6A2 2 0 0 1 18.8 20H9V9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ThumbDownIcon() {
  return (
    <svg className="quick-feedback__icon" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M17 14V4h3a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-3Zm-2 1-4.5 4.2a1.5 1.5 0 0 1-2.5-1.1V14H3.7a2 2 0 0 1-1.95-2.45l1.5-6A2 2 0 0 1 5.2 4H15v11Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M3 8.5 6.5 12 13 4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface QuickFeedbackPanelProps {
  rating: number | null;
  wouldUse: WouldUse;
  submitting: boolean;
  message: string | null;
  error: string | null;
  onThumbUp: () => void;
  onThumbDown: () => void;
  onSkip?: () => void;
  onStarClick: (value: number) => void;
  onWouldUseChange: (value: WouldUse) => void;
  comment: string;
  onCommentChange: (value: string) => void;
  onCommentBlur: () => void;
}

export function QuickFeedbackPanel({
  rating,
  wouldUse,
  submitting,
  message,
  error,
  onThumbUp,
  onThumbDown,
  onSkip,
  onStarClick,
  onWouldUseChange,
  comment,
  onCommentChange,
  onCommentBlur,
}: QuickFeedbackPanelProps) {
  const { t } = useTranslation();

  return (
    <section className="quick-feedback" aria-label={t("ideas.quickRatingLabel")}>
      <div className="quick-feedback__card">
        <p className="quick-feedback__prompt">{t("ideas.quickFeedbackPrompt")}</p>
        <p className="quick-feedback__hint">{t("ideas.quickFeedbackHint")}</p>

        <div className="quick-feedback__actions">
          <button
            type="button"
            className={`quick-feedback__thumb quick-feedback__thumb--up ${rating != null && rating >= 4 ? "quick-feedback__thumb--active" : ""}`}
            disabled={submitting}
            aria-pressed={rating != null && rating >= 4}
            onClick={onThumbUp}
          >
            <ThumbUpIcon />
            {t("ideas.useful")}
          </button>
          <button
            type="button"
            className={`quick-feedback__thumb quick-feedback__thumb--down ${rating != null && rating <= 2 ? "quick-feedback__thumb--active" : ""}`}
            disabled={submitting}
            aria-pressed={rating != null && rating <= 2}
            onClick={onThumbDown}
          >
            <ThumbDownIcon />
            {t("ideas.notUseful")}
          </button>
          {onSkip ? (
            <button type="button" className="quick-feedback__skip" disabled={submitting} onClick={onSkip}>
              {t("ideas.skipIdea")}
            </button>
          ) : null}
        </div>

        <div className="quick-feedback__refine">
          <span className="quick-feedback__refine-label">{t("ideas.orPickScore")}</span>
          <div className="quick-rating__stars quick-rating__stars--compact" role="group" aria-label={t("ideas.quickRatingLabel")}>
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                className={`quick-rating__star quick-rating__star--compact ${rating === value ? "quick-rating__star--selected" : ""} ${rating != null && rating >= value ? "quick-rating__star--filled" : ""}`}
                disabled={submitting}
                aria-label={t("ideas.rateValue", { value })}
                aria-pressed={rating === value}
                onClick={() => onStarClick(value)}
              >
                ★
              </button>
            ))}
          </div>
        </div>

        {rating != null ? (
          <div className="quick-rating__chips quick-rating__chips--inline">
            <span className="quick-rating__chips-label">{t("ideas.useInPaper")}</span>
            {(["yes", "maybe", "no"] as const).map((value) => (
              <button
                key={value}
                type="button"
                className={`quick-rating__chip ${wouldUse === value ? "quick-rating__chip--active" : ""}`}
                disabled={submitting}
                aria-pressed={wouldUse === value}
                onClick={() => onWouldUseChange(value)}
              >
                {t(`common.${value}`)}
              </button>
            ))}
          </div>
        ) : null}

        <Form.Group className="quick-rating__note quick-rating__note--inline">
          <Form.Label className="visually-hidden">{t("ideas.addNote")}</Form.Label>
          <Form.Control
            type="text"
            placeholder={t("ideas.notePlaceholder")}
            value={comment}
            onChange={(e) => onCommentChange(e.target.value)}
            onBlur={onCommentBlur}
            disabled={submitting}
          />
        </Form.Group>

        {message ? (
          <span className="quick-feedback__saved">
            <CheckIcon />
            {message}
          </span>
        ) : null}
        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
      </div>
    </section>
  );
}
