interface RunDetailSkeletonProps {
  /** Full page load vs ideas-only while run metadata is already shown */
  variant?: "full" | "ideas";
}

function Shimmer({ className }: { className: string }) {
  return <div className={`skeleton-shimmer ${className}`} aria-hidden />;
}

export function RunDetailSkeleton({ variant = "full" }: RunDetailSkeletonProps) {
  return (
    <div className="page-shell run-detail run-detail--skeleton" aria-busy="true" aria-live="polite">
      {variant === "full" ? (
        <header className="run-detail__header">
          <Shimmer className="skeleton-line skeleton-line--sm skeleton-line--w25" />
          <div className="run-detail__headline mt-2">
            <Shimmer className="skeleton-pill skeleton-pill--badge" />
            <Shimmer className="skeleton-pill skeleton-pill--date" />
          </div>
          <Shimmer className="skeleton-line skeleton-line--title mt-2" />
          <Shimmer className="skeleton-line skeleton-line--subtitle" />
        </header>
      ) : null}

      {variant === "full" ? (
        <div className="skeleton-panel mb-4">
          <Shimmer className="skeleton-line skeleton-line--sm skeleton-line--w75 mb-3" />
          <Shimmer className="skeleton-bar" />
          <Shimmer className="skeleton-line skeleton-line--xs skeleton-line--w50 mt-3" />
        </div>
      ) : null}

      <div className="skeleton-carousel mb-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Shimmer key={i} className="skeleton-dot" />
        ))}
      </div>

      <div className="skeleton-card">
        <div className="skeleton-card__meta">
          <Shimmer className="skeleton-pill" />
          <Shimmer className="skeleton-pill" />
          <Shimmer className="skeleton-pill" />
        </div>
        <Shimmer className="skeleton-line skeleton-line--heading mb-3" />
        <Shimmer className="skeleton-line skeleton-line--body" />
        <Shimmer className="skeleton-line skeleton-line--body" />
        <Shimmer className="skeleton-line skeleton-line--body skeleton-line--w75 mb-4" />
        <div className="skeleton-tabs">
          <Shimmer className="skeleton-tab" />
          <Shimmer className="skeleton-tab" />
          <Shimmer className="skeleton-tab" />
        </div>
        <Shimmer className="skeleton-feedback mt-4" />
      </div>
    </div>
  );
}
