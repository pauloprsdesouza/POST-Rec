import { useTranslation } from "react-i18next";

interface FeedbackProgressProps {
  ratedCount: number;
  total: number;
  onSkip?: () => void;
  onJumpToUnrated?: () => void;
}

export function FeedbackProgress({
  ratedCount,
  total,
  onSkip,
  onJumpToUnrated,
}: FeedbackProgressProps) {
  const { t } = useTranslation();
  const complete = ratedCount >= total;
  const pct = total > 0 ? Math.round((ratedCount / total) * 100) : 0;

  return (
    <div className={`feedback-progress ${complete ? "feedback-progress--complete" : ""}`}>
      <div className="feedback-progress__head">
        <span className="feedback-progress__label">
          {complete
            ? t("ideas.feedbackProgressComplete", { count: total })
            : t("ideas.feedbackProgress", { rated: ratedCount, total })}
        </span>
        {!complete && onJumpToUnrated ? (
          <button type="button" className="feedback-progress__link" onClick={onJumpToUnrated}>
            {t("ideas.jumpToUnrated")}
          </button>
        ) : null}
      </div>
      <div
        className="feedback-progress__bar"
        role="progressbar"
        aria-valuenow={ratedCount}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={t("ideas.feedbackProgress", { rated: ratedCount, total })}
      >
        <div className="feedback-progress__fill" style={{ width: `${pct}%` }} />
      </div>
      {!complete && onSkip ? (
        <button type="button" className="feedback-progress__skip" onClick={onSkip}>
          {t("ideas.skipIdea")}
        </button>
      ) : null}
    </div>
  );
}
