import type { ReactNode } from "react";

import type { RunOutcome } from "@/features/runs/utils/runs";

interface RunSectionProps {
  title: string;
  description?: string;
  count: number;
  variant?: RunOutcome | "other";
  dataCoach?: string;
  children: ReactNode;
}

const VARIANT_CLASS: Record<string, string> = {
  ready: "run-section--ready",
  in_progress: "run-section--active",
  failed: "run-section--failed",
  incomplete: "run-section--other",
  other: "run-section--other",
};

export function RunSection({ title, description, count, variant = "other", dataCoach, children }: RunSectionProps) {
  if (count === 0) {
    return null;
  }

  const variantClass = VARIANT_CLASS[variant] ?? VARIANT_CLASS.other;

  return (
    <section className={`run-section panel ${variantClass}`} {...(dataCoach ? { "data-coach": dataCoach } : {})}>
      <header className="panel__header run-section__header">
        <div className="run-section__header-text">
          <h2 className="panel__title run-section__heading">{title}</h2>
          {description ? <p className="panel__desc run-section__desc">{description}</p> : null}
        </div>
        <span className="run-section__badge" aria-label={String(count)}>
          {count}
        </span>
      </header>
      <div className="run-section__list">{children}</div>
    </section>
  );
}
