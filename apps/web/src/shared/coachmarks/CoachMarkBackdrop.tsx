import { useId } from "react";

import type { TargetRect } from "./positioning";

interface CoachMarkBackdropProps {
  targetRect: TargetRect | null;
  onSkip: () => void;
  label: string;
}

export function CoachMarkBackdrop({ targetRect, onSkip, label }: CoachMarkBackdropProps) {
  const maskId = `coach-mask-${useId().replace(/[^a-zA-Z0-9-_]/g, "")}`;

  if (!targetRect) {
    return (
      <button
        type="button"
        className="coach-mark__backdrop coach-mark__backdrop--full"
        aria-label={label}
        onClick={onSkip}
      />
    );
  }

  return (
    <button
      type="button"
      className="coach-mark__backdrop"
      aria-label={label}
      onClick={onSkip}
    >
      <svg className="coach-mark__backdrop-svg" aria-hidden>
        <defs>
          <mask id={maskId}>
            <rect width="100%" height="100%" fill="white" />
            <rect
              x={targetRect.left}
              y={targetRect.top}
              width={targetRect.width}
              height={targetRect.height}
              rx={targetRect.radius}
              ry={targetRect.radius}
              fill="black"
            />
          </mask>
        </defs>
        <rect width="100%" height="100%" className="coach-mark__backdrop-fill" mask={`url(#${maskId})`} />
      </svg>
    </button>
  );
}
