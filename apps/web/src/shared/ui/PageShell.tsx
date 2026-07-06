import type { HTMLAttributes, ReactNode } from "react";

export type PageShellWidth = "default" | "narrow" | "wide" | "list";

export interface PageShellProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  width?: PageShellWidth;
  withStickyFooter?: boolean;
  pageClass?: string;
}

function joinClasses(...parts: Array<string | false | undefined | null>) {
  return parts.filter(Boolean).join(" ");
}

const WIDTH_CLASS: Record<PageShellWidth, string | undefined> = {
  default: undefined,
  narrow: "page-shell--narrow",
  wide: "page-shell--wide",
  list: "page-shell--list",
};

export function PageShell({
  children,
  width = "default",
  withStickyFooter = false,
  className,
  pageClass,
  ...rest
}: PageShellProps) {
  return (
    <div
      className={joinClasses(
        "page-shell",
        WIDTH_CLASS[width],
        withStickyFooter && "page-shell--with-sticky-footer",
        pageClass,
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
