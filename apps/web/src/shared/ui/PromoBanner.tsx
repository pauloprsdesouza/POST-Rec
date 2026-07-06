import type { ReactNode } from "react";

export type PromoBannerVariant = "default" | "success" | "step";

export interface PromoBannerProps {
  id?: string;
  badge?: ReactNode;
  message?: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  footnote?: ReactNode;
  icon?: ReactNode;
  variant?: PromoBannerVariant;
  header?: ReactNode;
  className?: string;
  role?: "status" | "region";
}

function joinClasses(...parts: Array<string | false | undefined | null>) {
  return parts.filter(Boolean).join(" ");
}

export function PromoBanner({
  id,
  badge,
  message,
  title,
  description,
  actions,
  footnote,
  icon,
  variant = "default",
  header,
  className,
  role = "region",
}: PromoBannerProps) {
  if (variant === "step") {
    return (
      <aside
        className={joinClasses("promo-banner", "promo-banner--step", className)}
        aria-labelledby={id}
        role={role}
      >
        {icon ? (
          <div className="promo-banner__icon" aria-hidden>
            {icon}
          </div>
        ) : null}
        <div className="promo-banner__copy">
          {title ? <p className="promo-banner__title">{title}</p> : null}
          {description ? <p className="promo-banner__desc">{description}</p> : null}
        </div>
        {actions}
        {footnote ? <p className="promo-banner__footnote">{footnote}</p> : null}
      </aside>
    );
  }

  return (
    <aside
      className={joinClasses(
        "promo-banner",
        variant === "success" && "promo-banner--success",
        className,
      )}
      aria-labelledby={id}
      role={role}
    >
      <div className="promo-banner__inner">
        {header}
        <div className="promo-banner__row">
          <div className="promo-banner__copy">
            {badge ? <span className="promo-banner__badge">{badge}</span> : null}
            {title ? (
              <p id={id} className="promo-banner__title">
                {title}
              </p>
            ) : null}
            {message ? (
              <p id={id} className="promo-banner__message">
                {message}
              </p>
            ) : null}
            {description ? <p className="promo-banner__desc">{description}</p> : null}
          </div>
          {actions ? <div className="promo-banner__actions">{actions}</div> : null}
        </div>
      </div>
    </aside>
  );
}
