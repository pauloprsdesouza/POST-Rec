import type { ReactNode } from "react";

interface TransparencySectionProps {
  id: string;
  title: string;
  intro?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function TransparencySection({
  id,
  title,
  intro,
  collapsible = false,
  defaultOpen = true,
  children,
}: TransparencySectionProps) {
  const body = (
    <>
      {intro ? <p className="transparency-section__intro">{intro}</p> : null}
      <div className="transparency-section__body">{children}</div>
    </>
  );

  if (collapsible) {
    return (
      <details
        id={id}
        className="transparency-section panel transparency-section--collapsible"
        open={defaultOpen}
      >
        <summary className="transparency-section__title">{title}</summary>
        {body}
      </details>
    );
  }

  return (
    <section id={id} className="transparency-section panel">
      <h2 className="transparency-section__title">{title}</h2>
      {body}
    </section>
  );
}
