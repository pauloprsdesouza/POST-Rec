import { findTargetElement, isElementVisible } from "./positioning";
import type { CoachMarkStep } from "./types";

export function resolveTourSteps(steps: CoachMarkStep[]): CoachMarkStep[] {
  return steps.filter((step) => {
    const element = findTargetElement(step.target, step.targetPreference);
    if (!element) {
      return false;
    }
    if (step.skipIfHidden && !isElementVisible(element)) {
      return false;
    }
    return true;
  });
}
