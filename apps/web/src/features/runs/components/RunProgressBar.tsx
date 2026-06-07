type RunProgressTone = "default" | "success" | "danger";

interface RunProgressBarProps {
  value: number;
  tone?: RunProgressTone;
  label?: string;
}

export function RunProgressBar({ value, tone = "default", label }: RunProgressBarProps) {
  const pct = Math.min(Math.max(value, 0), 100);

  return (
    <div className="run-progress-bar-wrap">
      <div className="run-progress-bar-wrap__head">
        <span className="run-progress-bar-wrap__label">{label ?? `${pct}%`}</span>
        <span className="run-progress-bar-wrap__value">{pct}%</span>
      </div>
      <div
        className="run-progress-bar"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className={`run-progress-bar__fill run-progress-bar__fill--${tone}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
