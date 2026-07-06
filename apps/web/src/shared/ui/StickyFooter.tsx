import type { ReactNode } from "react";

export type StickyFooterVariant = "fixed" | "dock";

export interface StickyFooterProps {
  variant: StickyFooterVariant;
  children: ReactNode;
  className?: string;
  visibleClass?: string;
}

function joinClasses(...parts: Array<string | false | undefined | null>) {
  return parts.filter(Boolean).join(" ");
}

export function StickyFooter({ variant, children, className, visibleClass }: StickyFooterProps) {
  return (
    <div
      className={joinClasses(
        "sticky-footer",
        variant === "fixed" ? "sticky-footer--fixed" : "sticky-footer--dock",
        visibleClass,
        className,
      )}
    >
      {children}
    </div>
  );
}
