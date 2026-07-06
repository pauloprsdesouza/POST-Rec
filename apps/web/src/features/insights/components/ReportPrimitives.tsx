import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { NarrativeTone } from "@/features/insights/utils/reportNarrative";
import { Panel } from "@/shared/ui/Panel";

export function ReportChapter({
  number,
  title,
  lead,
  children,
  id,
}: {
  number: number;
  title: string;
  lead: string;
  children: ReactNode;
  id?: string;
}) {
  return (
    <Panel as="section" className="research-report__chapter" id={id}>
      <div className="research-report__chapter-header">
        <span className="research-report__chapter-number">
          {String(number).padStart(2, "0")}
        </span>
        <div>
          <h2 className="research-report__chapter-title">{title}</h2>
          <p className="research-report__chapter-lead">{lead}</p>
        </div>
      </div>
      <div className="research-report__chapter-body">{children}</div>
    </Panel>
  );
}

export function StoryAtAGlance({
  eyebrow,
  headline,
  subheadline,
  children,
}: {
  eyebrow: string;
  headline: string;
  subheadline: string;
  children: ReactNode;
}) {
  return (
    <Panel as="section" className="research-report__glance" id="story">
      <p className="research-report__glance-eyebrow">{eyebrow}</p>
      <h2 className="research-report__glance-headline">{headline}</h2>
      <p className="research-report__glance-subheadline">{subheadline}</p>
      <div className="research-report__glance-grid">{children}</div>
    </Panel>
  );
}

export function StoryCard({
  label,
  value,
  story,
  tone = "neutral",
}: {
  label: string;
  value: string;
  story: string;
  tone?: NarrativeTone;
}) {
  return (
    <article className={`research-report__story-card research-report__story-card--${tone}`}>
      <span className="research-report__story-card-label">{label}</span>
      <span className="research-report__story-card-value">{value}</span>
      <p className="research-report__story-card-story">{story}</p>
    </article>
  );
}

export function NarrativeCallout({ children, tone = "neutral" }: { children: ReactNode; tone?: NarrativeTone }) {
  return (
    <div className={`research-report__callout research-report__callout--${tone}`}>{children}</div>
  );
}

export function ReportTableOfContents({
  items,
}: {
  items: { id: string; label: string }[];
}) {
  if (!items.length) {
    return null;
  }

  return (
    <Panel as="nav" className="research-report__toc" aria-label="Report sections">
      <p className="research-report__toc-title">In this report</p>
      <ol className="research-report__toc-list">
        {items.map((item) => (
          <li key={item.id}>
            <a href={`#${item.id}`}>{item.label}</a>
          </li>
        ))}
      </ol>
    </Panel>
  );
}

export function CollapsibleBlock({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="research-report__collapsible">
      <button
        type="button"
        className="research-report__collapsible-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span>{title}</span>
        <span className="research-report__collapsible-icon" aria-hidden>
          {open ? t("researchReport.story.hideDetails") : t("researchReport.story.showDetails")}
        </span>
      </button>
      {open ? <div className="research-report__collapsible-body">{children}</div> : null}
    </div>
  );
}

export function ReportSection({
  title,
  subtitle,
  children,
  id,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  id?: string;
}) {
  return (
    <Panel
      as="section"
      className="research-report__section"
      id={id}
      title={title}
      subtitle={subtitle}
      headingLevel="h2"
    >
      {children}
    </Panel>
  );
}

export function StatGrid({ children }: { children: ReactNode }) {
  return <div className="research-report__stat-grid">{children}</div>;
}

export function StatCard({
  label,
  value,
  hint,
  highlight = false,
}: {
  label: string;
  value: string;
  hint?: string;
  highlight?: boolean;
}) {
  return (
    <div className={`research-report__stat ${highlight ? "research-report__stat--highlight" : ""}`}>
      <span className="research-report__stat-label">{label}</span>
      <span className="research-report__stat-value">{value}</span>
      {hint ? <span className="research-report__stat-hint">{hint}</span> : null}
    </div>
  );
}

export function DataTable({
  columns,
  rows,
  emptyMessage,
}: {
  columns: { key: string; label: string; align?: "left" | "right" }[];
  rows: Record<string, string | number | null | undefined>[];
  emptyMessage?: string;
}) {
  if (!rows.length) {
    return emptyMessage ? <p className="text-muted mb-0">{emptyMessage}</p> : null;
  }

  return (
    <div className="table-responsive">
      <table className="table table-sm research-report__table mb-0">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={col.align === "right" ? "text-end" : undefined}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((col) => (
                <td key={col.key} className={col.align === "right" ? "text-end" : undefined}>
                  {row[col.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SignificanceBadge({ significant }: { significant: boolean }) {
  const { t } = useTranslation();
  return (
    <span className={`research-report__sig ${significant ? "research-report__sig--yes" : "research-report__sig--no"}`}>
      {significant ? t("researchReport.story.significant") : t("researchReport.story.notSignificant")}
    </span>
  );
}
