import type { ReactNode } from "react";

interface SectionGroupProps {
  title: string;
  intro?: string;
  children: ReactNode;
  className?: string;
  headingLevel?: "h2" | "h3";
}

export function SectionGroup({
  title,
  intro,
  children,
  className = "",
  headingLevel = "h3",
}: SectionGroupProps) {
  const Heading = headingLevel;

  return (
    <section className={`section-group ${className}`.trim()}>
      <header className="section-group__header">
        <Heading className="section-group__title">{title}</Heading>
        {intro ? <p className="section-group__intro">{intro}</p> : null}
      </header>
      <div className="section-group__content">{children}</div>
    </section>
  );
}
