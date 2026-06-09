export type CoachMarkTourId = "runsHome" | "newRun" | "runReview" | "profile" | "insights";

export type CoachMarkPlacement = "top" | "bottom" | "left" | "right" | "auto";
export type CoachMarkAlign = "start" | "center" | "end";
export type CoachMarkTargetPreference = "first-visible" | "largest" | "bottom-most";

export interface CoachMarkStep {
  target: string;
  titleKey: string;
  bodyKey: string;
  placement?: CoachMarkPlacement;
  align?: CoachMarkAlign;
  targetPreference?: CoachMarkTargetPreference;
  skipIfHidden?: boolean;
  spotlightPadding?: number;
}

export interface CoachMarkTour {
  id: CoachMarkTourId;
  steps: CoachMarkStep[];
}
