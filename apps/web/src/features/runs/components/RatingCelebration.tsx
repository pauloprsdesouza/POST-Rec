import { useEffect } from "react";

type CelebrationKind = "first" | "all";

interface RatingCelebrationProps {
  kind: CelebrationKind | null;
  onDismiss: () => void;
  message: string;
}

export function RatingCelebration({ kind, onDismiss, message }: RatingCelebrationProps) {
  useEffect(() => {
    if (!kind) {
      return;
    }
    const timer = window.setTimeout(onDismiss, 2800);
    return () => window.clearTimeout(timer);
  }, [kind, onDismiss]);

  if (!kind) {
    return null;
  }

  return (
    <div
      className={`rating-celebration rating-celebration--${kind}`}
      role="status"
      aria-live="polite"
    >
      <span className="rating-celebration__icon" aria-hidden>
        {kind === "all" ? "★" : "✓"}
      </span>
      <span className="rating-celebration__text">{message}</span>
    </div>
  );
}
