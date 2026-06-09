import type { ReactNode } from "react";

interface RunSectionProps {
  title: string;
  description?: string;
  count: number;
  dataCoach?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  children: ReactNode;
}

function SectionHeader({
  title,
  description,
  count,
}: {
  title: string;
  description?: string;
  count: number;
}) {
  return (
    <div className="run-section__intro">
      <div className="run-section__head">
        <h2 className="run-section__title">{title}</h2>
        <span className="run-section__count" aria-label={String(count)}>
          {count}
        </span>
      </div>
      {description ? <p className="run-section__desc">{description}</p> : null}
    </div>
  );
}

export function RunSection({
  title,
  description,
  count,
  dataCoach,
  collapsible = false,
  defaultOpen = true,
  children,
}: RunSectionProps) {
  if (count === 0) {
    return null;
  }

  if (collapsible && !defaultOpen) {
    return (
      <details
        className="run-section run-section--collapse"
        {...(dataCoach ? { "data-coach": dataCoach } : {})}
      >
        <summary className="run-section__summary">
          <SectionHeader title={title} description={description} count={count} />
        </summary>
        <ul className="runs-list">{children}</ul>
      </details>
    );
  }

  return (
    <section className="run-section" {...(dataCoach ? { "data-coach": dataCoach } : {})}>
      <SectionHeader title={title} description={description} count={count} />
      <ul className="runs-list">{children}</ul>
    </section>
  );
}
