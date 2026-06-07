import type { ReactNode } from "react";

import { EmptyIllustration, type EmptyIllustrationVariant } from "./illustrations/EmptyIllustration";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  variant?: EmptyIllustrationVariant;
}

export function EmptyState({ title, description, action, variant = "runs" }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <EmptyIllustration variant={variant} className="empty-state__art" />
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__description">{description}</p>
      {action ? <div className="empty-state__action">{action}</div> : null}
    </div>
  );
}
