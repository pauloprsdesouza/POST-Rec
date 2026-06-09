interface ScoreBarProps {
  label: string;
  value: number;
  /** When true, bar width reflects (100 - value) but label still shows raw value. */
  invert?: boolean;
}

export function ScoreBar({ label, value, invert = false }: ScoreBarProps) {
  const clamped = Math.min(Math.max(value, 0), 100);
  const shown = invert ? Math.max(0, 100 - clamped) : clamped;

  return (
    <div className="idea-scores__item">
      <div className="idea-scores__label">
        <span className="idea-scores__name">{label}</span>
        <span className="idea-scores__value">{Math.round(shown)}</span>
      </div>
      <div className="idea-scores__track" role="presentation" aria-hidden>
        <div className="idea-scores__fill" style={{ width: `${shown}%` }} />
      </div>
    </div>
  );
}
