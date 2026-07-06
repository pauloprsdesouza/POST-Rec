import { useTranslation } from "react-i18next";

import { InlineAlert } from "@/shared/ui/InlineAlert";

export type WouldUse = "yes" | "maybe" | "no";

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
  onStarClick: (value: number) => void;
  onWouldUseChange: (value: WouldUse) => void;
}

export function QuickFeedbackPanel({
  rating,
  wouldUse,
  submitting,
  message,
  error,
  onStarClick,
  onWouldUseChange,
}: QuickFeedbackPanelProps) {
  const { t } = useTranslation();

  return (
    <section className="quick-feedback" aria-label={t("ideas.quickRatingLabel")}>
      <div className="quick-feedback__card">
        <div className="quick-feedback__field">
          <span className="quick-feedback__field-label">{t("ideas.quickRatingLabel")}</span>
          <div className="quick-rating__stars" role="group" aria-label={t("ideas.quickRatingLabel")}>
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                className={`quick-rating__star ${rating === value ? "quick-rating__star--selected" : ""} ${rating != null && rating >= value ? "quick-rating__star--filled" : ""}`}
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

        <div className="quick-feedback__field">
          <span className="quick-feedback__field-label">{t("ideas.useInPaper")}</span>
          <div className="quick-rating__chips quick-rating__chips--inline">
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
        </div>

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
