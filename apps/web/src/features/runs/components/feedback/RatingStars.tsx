interface RatingStarsProps {
  value: number | null;
  disabled?: boolean;
  ariaLabel: string;
  getStarLabel: (value: number) => string;
  onChange: (value: number) => void;
}

export function RatingStars({
  value,
  disabled = false,
  ariaLabel,
  getStarLabel,
  onChange,
}: RatingStarsProps) {
  return (
    <div className="rating-stars" role="group" aria-label={ariaLabel}>
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = value != null && value >= star;
        const selected = value === star;

        return (
          <button
            key={star}
            type="button"
            className={`rating-stars__btn ${filled ? "rating-stars__btn--filled" : ""} ${selected ? "rating-stars__btn--selected" : ""}`}
            disabled={disabled}
            aria-label={getStarLabel(star)}
            aria-pressed={selected}
            onClick={() => onChange(star)}
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
