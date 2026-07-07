import type { ReactNode } from "react";

interface FeedbackFieldProps {
  label: string;
  children: ReactNode;
}

export function FeedbackField({ label, children }: FeedbackFieldProps) {
  return (
    <div className="feedback-field">
      <p className="feedback-field__label">{label}</p>
      <div className="feedback-field__control">{children}</div>
    </div>
  );
}
