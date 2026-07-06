interface ProgressRingProps {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  variant?: "primary" | "success";
  className?: string;
}

export function ProgressRing({
  value,
  size = 88,
  stroke = 7,
  label,
  sublabel,
  variant = "primary",
  className = "",
}: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const center = size / 2;

  return (
    <div
      className={`progress-ring progress-ring--${variant} ${className}`.trim()}
      style={{ width: size, height: size }}
      role="img"
      aria-label={label ? `${label}${sublabel ? `, ${sublabel}` : ""}` : `${clamped}%`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle
          className="progress-ring__track"
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          className="progress-ring__fill"
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${center} ${center})`}
        />
      </svg>
      <div className="progress-ring__content">
        <span className="progress-ring__value">{Math.round(clamped)}%</span>
        {sublabel ? <span className="progress-ring__sublabel">{sublabel}</span> : null}
      </div>
    </div>
  );
}
