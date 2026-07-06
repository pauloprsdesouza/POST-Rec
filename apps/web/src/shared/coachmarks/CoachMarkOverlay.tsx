import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

import { CoachMarkBackdrop } from "./CoachMarkBackdrop";
import {
  computePopoverLayout,
  findTargetElement,
  isElementVisible,
  isTargetInComfortZone,
  measureTarget,
  type PopoverLayout,
  type TargetRect,
} from "./positioning";
import type { CoachMarkStep, CoachMarkTourId } from "./types";
import { releaseOverflowClipping } from "./targetElevation";
import { getViewportInsets } from "./viewport";

interface CoachMarkOverlayProps {
  tourId: CoachMarkTourId;
  steps: CoachMarkStep[];
  stepIndex: number;
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

function scrollTargetIntoView(element: HTMLElement): void {
  const insets = getViewportInsets();

  if (isTargetInComfortZone(measureTarget(element, 0), insets)) {
    return;
  }

  element.scrollIntoView({
    block: "center",
    inline: "nearest",
    behavior: "smooth",
  });
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
  const popoverRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);
  const activeTargetRef = useRef<HTMLElement | null>(null);
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const [popoverLayout, setPopoverLayout] = useState<PopoverLayout | null>(null);
  const [missingTarget, setMissingTarget] = useState(false);
  const [ready, setReady] = useState(false);
  const [animating, setAnimating] = useState(false);

  const updateLayout = useCallback(() => {
    if (!step) {
      setTargetRect(null);
      setPopoverLayout(null);
      setMissingTarget(false);
      setReady(false);
      return;
    }

    const element = findTargetElement(step.target, step.targetPreference);
    if (!element || (step.skipIfHidden && !isElementVisible(element))) {
      setMissingTarget(true);
      setTargetRect(null);
      setPopoverLayout(null);
      setReady(false);
      return;
    }

    activeTargetRef.current = element;
    setMissingTarget(false);
    const measuredTarget = measureTarget(element, step.spotlightPadding ?? 10);
    setTargetRect(measuredTarget);

    const popoverWidth = popoverRef.current?.offsetWidth ?? 304;
    const popoverHeight = popoverRef.current?.offsetHeight ?? 220;
    setPopoverLayout(
      computePopoverLayout(
        measuredTarget,
        step.placement ?? "auto",
        step.align ?? "center",
        getViewportInsets(),
        popoverWidth,
        popoverHeight,
      ),
    );
    setReady(true);
  }, [step]);

  useLayoutEffect(() => {
    if (!step) {
      return;
    }

    setAnimating(true);
    const animationTimer = window.setTimeout(() => setAnimating(false), 220);

    const element = findTargetElement(step.target, step.targetPreference);
    if (!element || (step.skipIfHidden && !isElementVisible(element))) {
      setMissingTarget(true);
      return;
    }

    setMissingTarget(false);
    scrollTargetIntoView(element);

    let frame = 0;
    const measureAfterScroll = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => {
        window.requestAnimationFrame(updateLayout);
      });
    };

    measureAfterScroll();
    const settleTimer = window.setTimeout(updateLayout, 320);

    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(settleTimer);
      window.clearTimeout(animationTimer);
    };
  }, [step, stepIndex, tourId, updateLayout]);

  useLayoutEffect(() => {
    if (!ready) {
      return;
    }
    updateLayout();
  }, [ready, updateLayout]);

  useEffect(() => {
    if (!step) {
      return;
    }

    const element = findTargetElement(step.target, step.targetPreference);
    document
      .querySelectorAll("[data-coach].coach-mark-target--active")
      .forEach((node) => node.classList.remove("coach-mark-target--active"));

    if (!element) {
      return;
    }

    element.classList.add("coach-mark-target--active");
    const releaseOverflow = releaseOverflowClipping(element);

    return () => {
      element.classList.remove("coach-mark-target--active");
      releaseOverflow();
    };
  }, [step, stepIndex]);

  useEffect(() => {
    const element = activeTargetRef.current;
    if (!element) {
      return;
    }

    const observer = new ResizeObserver(() => updateLayout());
    observer.observe(element);
    return () => observer.disconnect();
  }, [step, stepIndex, updateLayout]);

  useEffect(() => {
    if (!missingTarget) {
      return;
    }
    const timer = window.setTimeout(onNext, 60);
    return () => window.clearTimeout(timer);
  }, [missingTarget, onNext]);

  useEffect(() => {
    const handleViewportChange = () => updateLayout();
    window.addEventListener("resize", handleViewportChange);
    window.addEventListener("scroll", handleViewportChange, true);
    return () => {
      window.removeEventListener("resize", handleViewportChange);
      window.removeEventListener("scroll", handleViewportChange, true);
    };
  }, [updateLayout]);

  useEffect(() => {
    document.body.classList.add("coach-mark-active");
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.classList.remove("coach-mark-active");
      document.body.style.overflow = previous;
    };
  }, []);

  useEffect(() => {
    if (!ready) {
      return;
    }
    nextButtonRef.current?.focus({ preventScroll: true });
  }, [stepIndex, ready]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onSkip();
        return;
      }
      if (event.key === "ArrowRight" || event.key === "Enter") {
        event.preventDefault();
        onNext();
        return;
      }
      if (event.key === "ArrowLeft" && stepIndex > 0) {
        event.preventDefault();
        onBack();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onBack, onNext, onSkip, stepIndex]);

  if (!step) {
    return null;
  }

  const isFirst = stepIndex === 0;
  const isLast = stepIndex === steps.length - 1;
  const placement = popoverLayout?.placement ?? "bottom";
  const docked = popoverLayout?.docked ?? false;
  const insets = getViewportInsets();

  const popoverStyle: React.CSSProperties = popoverLayout
    ? docked
      ? {
          left: insets.left,
          right: insets.right,
          bottom: popoverLayout.dockBottom ?? insets.bottom,
          width: "auto",
          maxHeight: `min(70dvh, calc(100dvh - ${insets.top}px - ${(popoverLayout.dockBottom ?? insets.bottom) + 12}px))`,
          overflowY: "auto",
          visibility: ready ? "visible" : "hidden",
        }
      : {
          top: popoverLayout.top,
          left: popoverLayout.left,
          width: popoverLayout.width,
          visibility: ready ? "visible" : "hidden",
        }
    : {
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        visibility: missingTarget ? "hidden" : "visible",
      };

  return createPortal(
    <div className="coach-mark" role="dialog" aria-modal="true" aria-labelledby="coach-mark-title">
      <CoachMarkBackdrop targetRect={targetRect} onSkip={onSkip} label={t("coachmarks.skip")} />
      {targetRect ? (
        <div
          className={`coach-mark__ring ${animating ? "coach-mark__ring--enter" : ""}`}
          style={{
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
            borderRadius: targetRect.radius,
          }}
          aria-hidden
        />
      ) : null}
      <div
        ref={popoverRef}
        className={[
          "coach-mark__popover",
          `coach-mark__popover--${placement}`,
          docked ? "coach-mark__popover--docked" : "",
          animating ? "coach-mark__popover--enter" : "",
          ready ? "coach-mark__popover--ready" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={popoverStyle}
      >
        {docked ? <div className="coach-mark__grabber" aria-hidden /> : null}
        {!docked && popoverLayout ? (
          <span
            className="coach-mark__arrow"
            style={
              placement === "top" || placement === "bottom"
                ? { left: popoverLayout.arrowOffset }
                : { top: popoverLayout.arrowOffset }
            }
            aria-hidden
          />
        ) : null}
        <div className="coach-mark__header">
          <div
            className="coach-mark__dots"
            role="tablist"
            aria-label={t("coachmarks.progress", { current: stepIndex + 1, total: steps.length })}
          >
            {steps.map((_, index) => (
              <span
                key={index}
                className={[
                  "coach-mark__dot",
                  index === stepIndex ? "coach-mark__dot--active" : "",
                  index < stepIndex ? "coach-mark__dot--done" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-current={index === stepIndex ? "step" : undefined}
              />
            ))}
          </div>
          <p className="coach-mark__progress">
            {t("coachmarks.progress", { current: stepIndex + 1, total: steps.length })}
          </p>
        </div>
        <div key={`${tourId}-${stepIndex}`} className="coach-mark__content">
          <h2 id="coach-mark-title" className="coach-mark__title">
            {t(step.titleKey)}
          </h2>
          <p className="coach-mark__body">{t(step.bodyKey)}</p>
        </div>
        <div className="coach-mark__actions">
          <button type="button" className="coach-mark__skip" onClick={onSkip}>
            {t("coachmarks.skip")}
          </button>
          <div className="coach-mark__nav">
            {!isFirst ? (
              <button type="button" className="btn btn-outline-secondary coach-mark__btn" onClick={onBack}>
                {t("coachmarks.back")}
              </button>
            ) : null}
            <button
              ref={nextButtonRef}
              type="button"
              className="btn btn-primary coach-mark__btn"
              onClick={onNext}
            >
              {isLast ? t("coachmarks.done") : t("coachmarks.next")}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
