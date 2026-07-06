import type { ReactNode } from "react";

import { Panel } from "@/shared/ui/Panel";

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
      <Panel
        as="details"
        id={id}
        className="transparency-section transparency-section--collapsible"
        open={defaultOpen}
      >
        <summary className="transparency-section__title">{title}</summary>
        {body}
      </Panel>
    );
  }

  return (
    <Panel as="section" id={id} className="transparency-section">
      <h2 className="transparency-section__title">{title}</h2>
      {body}
    </Panel>
  );
}
