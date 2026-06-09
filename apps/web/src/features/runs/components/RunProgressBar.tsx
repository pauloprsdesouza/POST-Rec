type RunProgressTone = "default" | "success" | "danger";

interface RunProgressBarProps {
  value: number;
  tone?: RunProgressTone;
  label?: string;
  indeterminate?: boolean;
}

export function RunProgressBar({
  value,
  tone = "default",
  label,
  indeterminate = false,
}: RunProgressBarProps) {
  const pct = Math.min(Math.max(value, 0), 100);

  return (
    <div className="run-progress-bar-wrap">
      <div className="run-progress-bar-wrap__head">
        <span className="run-progress-bar-wrap__label">{label ?? `${pct}%`}</span>
        <span className="run-progress-bar-wrap__value">{pct}%</span>
      </div>
      <div
        className={`run-progress-bar${indeterminate ? " run-progress-bar--indeterminate" : ""}`}
        role="progressbar"
        aria-valuenow={indeterminate ? undefined : pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        aria-busy={indeterminate || undefined}
      >
        <div
          className={`run-progress-bar__fill run-progress-bar__fill--${tone}${indeterminate ? " run-progress-bar__fill--indeterminate" : ""}`}
          style={indeterminate ? undefined : { width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
