import type { ReactNode } from "react";

interface MathBlockProps {
  children: ReactNode;
  caption?: string;
}

export function MathBlock({ children, caption }: MathBlockProps) {
  return (
    <figure className="math-block">
      <div className="math-block__body">{children}</div>
      {caption ? <figcaption className="math-block__caption">{caption}</figcaption> : null}
    </figure>
  );
}
