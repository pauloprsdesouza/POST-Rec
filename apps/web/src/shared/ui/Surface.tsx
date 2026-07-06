import type { ReactNode } from "react";

export interface SurfaceProps {
  children: ReactNode;
  className?: string;
  asCard?: boolean;
}

function joinClasses(...parts: Array<string | false | undefined | null>) {
  return parts.filter(Boolean).join(" ");
}

export function Surface({ children, className, asCard = false }: SurfaceProps) {
  return (
    <div className={joinClasses(asCard ? "page-card surface-inset" : "surface-inset", className)}>
      {children}
    </div>
  );
}
