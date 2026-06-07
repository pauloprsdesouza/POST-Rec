import { useCallback, useEffect, useLayoutEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

import type { CoachMarkStep, CoachMarkTourId } from "./types";

interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface CoachMarkOverlayProps {
  tourId: CoachMarkTourId;
  steps: CoachMarkStep[];
  stepIndex: number;
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

function findTarget(target: string): HTMLElement | null {
  return document.querySelector<HTMLElement>(`[data-coach="${target}"]`);
}

function measureTarget(element: HTMLElement): TargetRect {
  const rect = element.getBoundingClientRect();
  const padding = 8;
  return {
    top: Math.max(rect.top - padding, 8),
    left: Math.max(rect.left - padding, 8),
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  };
}

export function CoachMarkOverlay({
  tourId,
  steps,
  stepIndex,
  onNext,
  onBack,
  onSkip,
}: CoachMarkOverlayProps) {
  const { t } = useTranslation();
  const step = steps[stepIndex];
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const [missingTarget, setMissingTarget] = useState(false);

  const updateRect = useCallback(() => {
    if (!step) {
      setTargetRect(null);
      return;
    }
    const element = findTarget(step.target);
    if (!element) {
      setMissingTarget(true);
      setTargetRect(null);
      return;
    }
    setMissingTarget(false);
    element.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
    window.setTimeout(() => {
      const refreshed = findTarget(step.target);
      if (refreshed) {
        setTargetRect(measureTarget(refreshed));
      }
    }, 200);
  }, [step]);

  useLayoutEffect(() => {
    updateRect();
  }, [updateRect, stepIndex, tourId]);

  useEffect(() => {
    const handleResize = () => updateRect();
    window.addEventListener("resize", handleResize);
    window.addEventListener("scroll", handleResize, true);
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("scroll", handleResize, true);
    };
  }, [updateRect]);

  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, []);

  if (!step) {
    return null;
  }

  const isFirst = stepIndex === 0;
  const isLast = stepIndex === steps.length - 1;

  const popoverStyle: React.CSSProperties = targetRect
    ? {
        top: Math.min(targetRect.top + targetRect.height + 12, window.innerHeight - 220),
        left: Math.min(Math.max(targetRect.left, 16), window.innerWidth - 320),
      }
    : {
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      };

  return createPortal(
    <div className="coach-mark" role="dialog" aria-modal="true" aria-labelledby="coach-mark-title">
      <button type="button" className="coach-mark__backdrop" aria-label={t("coachmarks.skip")} onClick={onSkip} />
      {targetRect ? (
        <div
          className="coach-mark__spotlight"
          style={{
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
          }}
        />
      ) : null}
      <div className="coach-mark__popover" style={popoverStyle}>
        <p className="coach-mark__progress">
          {t("coachmarks.progress", { current: stepIndex + 1, total: steps.length })}
        </p>
        <h2 id="coach-mark-title" className="coach-mark__title">
          {t(step.titleKey)}
        </h2>
        <p className="coach-mark__body">{t(step.bodyKey)}</p>
        {missingTarget ? <p className="coach-mark__hint">{t("coachmarks.targetMissing")}</p> : null}
        <div className="coach-mark__actions">
          <button type="button" className="coach-mark__skip" onClick={onSkip}>
            {t("coachmarks.skip")}
          </button>
          <div className="coach-mark__nav">
            {!isFirst ? (
              <button type="button" className="btn btn-outline-secondary btn-sm" onClick={onBack}>
                {t("coachmarks.back")}
              </button>
            ) : null}
            <button type="button" className="btn btn-primary btn-sm" onClick={onNext}>
              {isLast ? t("coachmarks.done") : t("coachmarks.next")}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
