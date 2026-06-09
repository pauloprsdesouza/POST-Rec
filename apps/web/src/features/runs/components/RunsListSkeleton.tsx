function Shimmer({ className }: { className: string }) {
  return <div className={`skeleton-shimmer ${className}`} aria-hidden />;
}

export function RunsListSkeleton() {
  return (
    <div className="runs-page runs-page--loading" aria-busy="true" aria-live="polite">
      <div className="page-stack">
        <header className="page-stack__block runs-page__header">
          <Shimmer className="skeleton-line skeleton-line--title" />
          <Shimmer className="skeleton-line skeleton-line--subtitle" />
          <div className="runs-page__toolbar">
            <Shimmer className="skeleton-line skeleton-line--body skeleton-line--w75" />
            <Shimmer className="segmented-control-skeleton" />
          </div>
        </header>

        <ul className="runs-list">
          {Array.from({ length: 4 }).map((_, i) => (
            <li key={i}>
              <div className="run-card run-card--skeleton">
                <div className="run-card__skeleton-body">
                  <Shimmer className="skeleton-pill skeleton-pill--badge mb-2" />
                  <Shimmer className="skeleton-line skeleton-line--heading mb-2" />
                  <Shimmer className="skeleton-line skeleton-line--body skeleton-line--w75" />
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
