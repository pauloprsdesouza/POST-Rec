import { ThumbDownIcon, ThumbUpIcon } from "./FeedbackThumbIcons";

interface BinaryFeedbackProps {
  disabled?: boolean;
  positiveLabel: string;
  negativeLabel: string;
  ariaLabel: string;
  onSelect: (positive: boolean) => void;
}

export function BinaryFeedback({
  disabled = false,
  positiveLabel,
  negativeLabel,
  ariaLabel,
  onSelect,
}: BinaryFeedbackProps) {
  return (
    <div className="binary-feedback" role="group" aria-label={ariaLabel}>
      <button
        type="button"
        className="binary-feedback__btn binary-feedback__btn--positive"
        disabled={disabled}
        aria-label={positiveLabel}
        onClick={() => onSelect(true)}
      >
        <ThumbUpIcon />
      </button>
      <button
        type="button"
        className="binary-feedback__btn binary-feedback__btn--negative"
        disabled={disabled}
        aria-label={negativeLabel}
        onClick={() => onSelect(false)}
      >
        <ThumbDownIcon />
      </button>
    </div>
  );
}
