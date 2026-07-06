import type { ViewportInsets } from "./viewport";
import type { CoachMarkAlign, CoachMarkPlacement, CoachMarkTargetPreference } from "./types";

export interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
  radius: number;
}

export interface PopoverLayout {
  top: number;
  left: number;
  width: number;
  placement: "top" | "bottom" | "left" | "right";
  arrowOffset: number;
  docked: boolean;
  /** Distance from viewport bottom for docked sheets (above tab bar / sticky chrome). */
  dockBottom?: number;
}

const GAP = 16;
const DEFAULT_POPOVER_WIDTH = 304;
const DEFAULT_POPOVER_HEIGHT = 220;
/** Align with SCSS `$bp-md` — mobile uses bottom-sheet coach UI (Apple HIG). */
export const MOBILE_SHEET_BREAKPOINT = 768;

export function isElementVisible(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return false;
  }

  const style = window.getComputedStyle(element);
  return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0;
}

export function findTargetElement(
  target: string,
  preference: CoachMarkTargetPreference = "first-visible",
): HTMLElement | null {
  const elements = [...document.querySelectorAll<HTMLElement>(`[data-coach="${target}"]`)];
  const visible = elements.filter(isElementVisible);

  if (!visible.length) {
    return null;
  }

  if (visible.length === 1 || preference === "first-visible") {
    return visible[0];
  }

  if (preference === "largest") {
    return visible.reduce((best, current) => {
      const bestArea = best.getBoundingClientRect().width * best.getBoundingClientRect().height;
      const currentArea = current.getBoundingClientRect().width * current.getBoundingClientRect().height;
      return currentArea > bestArea ? current : best;
    });
  }

  if (preference === "bottom-most") {
    return visible.reduce((best, current) =>
      current.getBoundingClientRect().bottom > best.getBoundingClientRect().bottom ? current : best,
    );
  }

  return visible[0];
}

function readBorderRadius(element: HTMLElement): number {
  const style = window.getComputedStyle(element);
  const radius = Number.parseFloat(style.borderRadius) || 0;
  return Math.min(radius || 8, 16);
}

export function measureTarget(element: HTMLElement, padding = 10): TargetRect {
  const rect = element.getBoundingClientRect();
  return {
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
    radius: readBorderRadius(element) + 2,
  };
}

function targetCenter(rect: TargetRect): { x: number; y: number } {
  return {
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2,
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function horizontalAlign(
  target: TargetRect,
  popoverWidth: number,
  align: CoachMarkAlign,
): number {
  if (align === "start") {
    return target.left;
  }
  if (align === "end") {
    return target.left + target.width - popoverWidth;
  }
  return target.left + target.width / 2 - popoverWidth / 2;
}

function verticalAlign(
  target: TargetRect,
  popoverHeight: number,
  align: CoachMarkAlign,
): number {
  if (align === "start") {
    return target.top;
  }
  if (align === "end") {
    return target.top + target.height - popoverHeight;
  }
  return target.top + target.height / 2 - popoverHeight / 2;
}

function popoverBounds(
  layout: Pick<PopoverLayout, "top" | "left" | "width">,
  popoverHeight: number,
): { top: number; left: number; right: number; bottom: number } {
  return {
    top: layout.top,
    left: layout.left,
    right: layout.left + layout.width,
    bottom: layout.top + popoverHeight,
  };
}

function overlapsTarget(
  layout: Pick<PopoverLayout, "top" | "left" | "width">,
  popoverHeight: number,
  target: TargetRect,
  gap = 6,
): boolean {
  const popover = popoverBounds(layout, popoverHeight);
  return !(
    popover.right + gap < target.left ||
    target.left + target.width + gap < popover.left ||
    popover.bottom + gap < target.top ||
    target.top + target.height + gap < popover.top
  );
}

function layoutForPlacement(
  target: TargetRect,
  placement: "top" | "bottom" | "left" | "right",
  align: CoachMarkAlign,
  popoverWidth: number,
  popoverHeight: number,
  insets: ViewportInsets,
): PopoverLayout {
  const center = targetCenter(target);
  let top: number;
  let left: number;

  if (placement === "bottom") {
    top = target.top + target.height + GAP;
    left = horizontalAlign(target, popoverWidth, align);
  } else if (placement === "top") {
    top = target.top - popoverHeight - GAP;
    left = horizontalAlign(target, popoverWidth, align);
  } else if (placement === "right") {
    left = target.left + target.width + GAP;
    top = verticalAlign(target, popoverHeight, align);
  } else {
    left = target.left - popoverWidth - GAP;
    top = verticalAlign(target, popoverHeight, align);
  }

  const maxLeft = window.innerWidth - popoverWidth - insets.right;
  const maxTop = window.innerHeight - popoverHeight - insets.bottom;
  left = clamp(left, insets.left, maxLeft);
  top = clamp(top, insets.top, maxTop);

  let arrowOffset: number;
  if (placement === "top" || placement === "bottom") {
    arrowOffset = clamp(center.x - left, 24, popoverWidth - 24);
  } else {
    arrowOffset = clamp(center.y - top, 24, popoverHeight - 24);
  }

  return {
    top,
    left,
    width: popoverWidth,
    placement,
    arrowOffset,
    docked: false,
  };
}

function scoreLayout(
  layout: PopoverLayout,
  preferred: CoachMarkPlacement,
  popoverHeight: number,
  target: TargetRect,
  insets: ViewportInsets,
): number {
  let score = 0;
  if (layout.placement === preferred) {
    score += 120;
  }

  const overflowBottom = Math.max(
    0,
    layout.top + popoverHeight - (window.innerHeight - insets.bottom),
  );
  const overflowTop = Math.max(0, insets.top - layout.top);
  const overflowRight = Math.max(
    0,
    layout.left + layout.width - (window.innerWidth - insets.right),
  );
  const overflowLeft = Math.max(0, insets.left - layout.left);
  score -= (overflowBottom + overflowTop + overflowRight + overflowLeft) * 6;

  if (overlapsTarget(layout, popoverHeight, target)) {
    score -= 200;
  }

  const center = targetCenter(target);
  const popoverCenterX = layout.left + layout.width / 2;
  const popoverCenterY = layout.top + popoverHeight / 2;
  const distance =
    layout.placement === "left" || layout.placement === "right"
      ? Math.abs(center.y - popoverCenterY)
      : Math.abs(center.x - popoverCenterX);
  score -= distance * 0.15;

  return score;
}

export function shouldUseDockedPopover(): boolean {
  return window.innerWidth < MOBILE_SHEET_BREAKPOINT;
}

export function computeDockedLayout(
  insets: ViewportInsets,
  popoverHeight: number,
  target?: TargetRect | null,
): PopoverLayout {
  const gap = 12;
  const width = window.innerWidth - insets.left - insets.right;
  const chromeTop = window.innerHeight - insets.bottom;

  let dockBottom = insets.bottom;

  if (target) {
    const targetCenterY = target.top + target.height / 2;
    const targetInLowerChrome = targetCenterY >= chromeTop - 48;

    if (targetInLowerChrome) {
      dockBottom = Math.max(insets.bottom, window.innerHeight - target.top + gap);
    } else if (target.top + target.height + gap + popoverHeight > chromeTop) {
      dockBottom = Math.max(insets.bottom, window.innerHeight - target.top + gap);
    }
  }

  const top = window.innerHeight - dockBottom - popoverHeight - gap;

  return {
    top: Math.max(insets.top, top),
    left: insets.left,
    width,
    placement: "top",
    arrowOffset: insets.left + width / 2,
    docked: true,
    dockBottom,
  };
}

export function computePopoverLayout(
  target: TargetRect,
  preferredPlacement: CoachMarkPlacement = "auto",
  align: CoachMarkAlign = "center",
  insets: ViewportInsets,
  popoverWidth = DEFAULT_POPOVER_WIDTH,
  popoverHeight = DEFAULT_POPOVER_HEIGHT,
): PopoverLayout {
  if (shouldUseDockedPopover()) {
    return computeDockedLayout(insets, popoverHeight, target);
  }

  const boundedWidth = Math.min(popoverWidth, window.innerWidth - insets.left - insets.right);
  const allPlacements: Array<"top" | "bottom" | "left" | "right"> = [
    "bottom",
    "top",
    "right",
    "left",
  ];
  const placements: Array<"top" | "bottom" | "left" | "right"> =
    preferredPlacement === "auto"
      ? allPlacements
      : [preferredPlacement, ...allPlacements].filter(
          (value, index, array): value is "top" | "bottom" | "left" | "right" =>
            array.indexOf(value) === index,
        );

  const ranked = placements
    .map((placement) =>
      layoutForPlacement(target, placement, align, boundedWidth, popoverHeight, insets),
    )
    .sort(
      (a, b) =>
        scoreLayout(b, preferredPlacement, popoverHeight, target, insets) -
        scoreLayout(a, preferredPlacement, popoverHeight, target, insets),
    );

  return ranked[0] ?? layoutForPlacement(target, "bottom", align, boundedWidth, popoverHeight, insets);
}

export function isTargetInComfortZone(target: TargetRect, insets: ViewportInsets): boolean {
  return (
    target.top >= insets.top &&
    target.left >= insets.left &&
    target.left + target.width <= window.innerWidth - insets.right &&
    target.top + target.height <= window.innerHeight - insets.bottom
  );
}
