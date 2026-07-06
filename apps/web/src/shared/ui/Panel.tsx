import type { HTMLAttributes, ReactNode } from "react";

export type PanelVariant = "default" | "emphasis" | "success";
export type PanelElement = "div" | "section" | "nav" | "aside" | "article" | "details" | "p";

export interface PanelProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  variant?: PanelVariant;
  title?: string;
  subtitle?: string;
  description?: string;
  headingLevel?: "h2" | "h3";
  as?: PanelElement;
  headerExtra?: ReactNode;
  open?: boolean;
}

function joinClasses(...parts: Array<string | false | undefined | null>) {
  return parts.filter(Boolean).join(" ");
}

const VARIANT_CLASS: Record<PanelVariant, string | undefined> = {
  default: undefined,
  emphasis: "panel--emphasis",
  success: "panel--success",
};

export function Panel({
  children,
  variant = "default",
  className,
  title,
  subtitle,
  description,
  headingLevel = "h3",
  as: Component = "div",
  headerExtra,
  ...rest
}: PanelProps) {
  const Heading = headingLevel;
  const hasHeader = Boolean(title || subtitle || description || headerExtra);

  return (
    <Component className={joinClasses("panel", VARIANT_CLASS[variant], className)} {...rest}>
      {hasHeader ? (
        <header className="panel__header">
          {title ? <Heading className="panel__title">{title}</Heading> : null}
          {subtitle ? <p className="panel__subtitle text-muted mb-0">{subtitle}</p> : null}
          {description ? <p className="panel__desc">{description}</p> : null}
          {headerExtra}
        </header>
      ) : null}
      {children}
    </Component>
  );
}
