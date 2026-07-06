import { useId } from "react";

import type { TargetRect } from "./positioning";

interface CoachMarkBackdropProps {
  targetRect: TargetRect | null;
  onSkip: () => void;
  label: string;
}

function viewportSize(): { width: number; height: number } {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export function CoachMarkBackdrop({ targetRect, onSkip, label }: CoachMarkBackdropProps) {
  const maskId = `coach-mask-${useId().replace(/[^a-zA-Z0-9-_]/g, "")}`;
  const { width, height } = viewportSize();

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
      <svg
        className="coach-mark__backdrop-svg"
        aria-hidden
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
      >
        <defs>
          <mask id={maskId}>
            <rect x={0} y={0} width={width} height={height} fill="white" />
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
        <rect
          x={0}
          y={0}
          width={width}
          height={height}
          className="coach-mark__backdrop-fill"
          mask={`url(#${maskId})`}
        />
      </svg>
    </button>
  );
}
