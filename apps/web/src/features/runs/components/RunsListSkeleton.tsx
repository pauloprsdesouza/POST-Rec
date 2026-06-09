function Shimmer({ className }: { className: string }) {
  return <div className={`skeleton-shimmer ${className}`} aria-hidden />;
}

export function RunsListSkeleton() {
  return (
    <div className="runs-page runs-page--loading" aria-busy="true" aria-live="polite">
      <div className="page-stack">
        <div className="page-stack__block">
          <Shimmer className="skeleton-line skeleton-line--title" />
          <Shimmer className="skeleton-line skeleton-line--subtitle" />
          <Shimmer className="skeleton-line skeleton-line--sm skeleton-line--w50" />
        </div>
        <Shimmer className="segmented-control-skeleton" />
        <div className="run-section__list">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="run-card run-card--skeleton">
              <div className="run-card__skeleton-body">
                <Shimmer className="skeleton-pill skeleton-pill--badge mb-2" />
                <Shimmer className="skeleton-line skeleton-line--heading mb-2" />
                <Shimmer className="skeleton-line skeleton-line--body skeleton-line--w75" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
