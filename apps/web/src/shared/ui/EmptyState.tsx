import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state text-center py-5 px-3">
      <h2 className="h4 mb-2">{title}</h2>
      <p className="empty-state__description mb-4">{description}</p>
      {action}
    </div>
  );
}
