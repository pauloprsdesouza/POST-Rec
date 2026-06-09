import type { ReactNode } from "react";

interface TransparencySectionProps {
  id: string;
  title: string;
  children: ReactNode;
}

export function TransparencySection({ id, title, children }: TransparencySectionProps) {
  return (
    <section id={id} className="transparency-section panel">
      <h2 className="transparency-section__title">{title}</h2>
      <div className="transparency-section__body">{children}</div>
    </section>
  );
}
