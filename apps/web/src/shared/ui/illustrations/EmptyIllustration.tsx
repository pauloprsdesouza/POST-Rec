export type EmptyIllustrationVariant = "runs" | "insights" | "feedback";

interface EmptyIllustrationProps {
  variant: EmptyIllustrationVariant;
  className?: string;
}

export function EmptyIllustration({ variant, className = "" }: EmptyIllustrationProps) {
  return (
    <div className={`empty-illustration empty-illustration--${variant} ${className}`.trim()} aria-hidden>
      {variant === "runs" ? <RunsIllustration /> : null}
      {variant === "insights" ? <InsightsIllustration /> : null}
      {variant === "feedback" ? <FeedbackIllustration /> : null}
    </div>
  );
}

function RunsIllustration() {
  return (
    <svg viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="28" y="48" width="88" height="104" rx="10" fill="var(--illus-surface)" stroke="var(--illus-border)" strokeWidth="1.5" />
      <rect x="40" y="64" width="48" height="4" rx="2" fill="var(--illus-muted)" opacity="0.5" />
      <rect x="40" y="76" width="64" height="4" rx="2" fill="var(--illus-muted)" opacity="0.35" />
      <rect x="40" y="88" width="56" height="4" rx="2" fill="var(--illus-muted)" opacity="0.35" />
      <rect x="40" y="100" width="40" height="4" rx="2" fill="var(--illus-muted)" opacity="0.25" />
      <rect x="84" y="24" width="88" height="104" rx="10" fill="var(--illus-surface)" stroke="var(--illus-accent)" strokeWidth="2" />
      <circle cx="128" cy="52" r="16" fill="var(--illus-accent-soft)" />
      <path
        d="M128 44v6l4 2"
        stroke="var(--illus-accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect x="96" y="76" width="64" height="4" rx="2" fill="var(--illus-muted)" opacity="0.4" />
      <rect x="96" y="88" width="48" height="4" rx="2" fill="var(--illus-muted)" opacity="0.3" />
      <rect x="96" y="100" width="56" height="4" rx="2" fill="var(--illus-muted)" opacity="0.3" />
      <path
        d="M52 36l12-12 12 12"
        stroke="var(--illus-accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
      <circle cx="164" cy="36" r="6" fill="var(--illus-accent-soft)" stroke="var(--illus-accent)" strokeWidth="1.5" />
    </svg>
  );
}

function InsightsIllustration() {
  return (
    <svg viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="24" y="32" width="152" height="104" rx="12" fill="var(--illus-surface)" stroke="var(--illus-border)" strokeWidth="1.5" />
      <rect x="48" y="108" width="16" height="28" rx="4" fill="var(--illus-accent-soft)" />
      <rect x="76" y="88" width="16" height="48" rx="4" fill="var(--illus-accent)" opacity="0.7" />
      <rect x="104" y="72" width="16" height="64" rx="4" fill="var(--illus-accent)" />
      <rect x="132" y="96" width="16" height="40" rx="4" fill="var(--illus-accent-soft)" />
      <path d="M44 56h112" stroke="var(--illus-border)" strokeWidth="1" strokeDasharray="4 4" />
      <circle cx="160" cy="48" r="14" fill="var(--illus-accent-soft)" stroke="var(--illus-accent)" strokeWidth="1.5" />
      <path d="M155 48h10M160 43v10" stroke="var(--illus-accent)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function FeedbackIllustration() {
  return (
    <svg viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="40" y="40" width="120" height="88" rx="14" fill="var(--illus-surface)" stroke="var(--illus-border)" strokeWidth="1.5" />
      {[56, 88, 120, 152].map((x, i) => (
        <path
          key={x}
          d={`M${x} 88 L${x - 6} 104 H${x + 6} Z`}
          fill={i < 2 ? "var(--illus-accent-soft)" : "var(--illus-muted)"}
          opacity={i < 2 ? 1 : 0.35}
        />
      ))}
      <circle cx="100" cy="68" r="18" fill="var(--illus-accent-soft)" stroke="var(--illus-accent)" strokeWidth="1.5" />
      <path
        d="M92 68c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8"
        stroke="var(--illus-accent)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path d="M88 76c2 3 5 4 12 4s10-1 12-4" stroke="var(--illus-accent)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
