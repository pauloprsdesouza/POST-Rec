import type { ReactNode } from "react";

interface InlineAlertProps {
  variant: "danger" | "warning" | "info" | "success";
  children: ReactNode;
  className?: string;
}

export function InlineAlert({ variant, children, className = "" }: InlineAlertProps) {
  return (
    <div className={`inline-alert inline-alert--${variant} ${className}`.trim()} role="alert">
      {children}
    </div>
  );
}
