export type CoachMarkTourId = "runsHome" | "newRun" | "runReview" | "profile" | "insights";

export interface CoachMarkStep {
  target: string;
  titleKey: string;
  bodyKey: string;
}

export interface CoachMarkTour {
  id: CoachMarkTourId;
  steps: CoachMarkStep[];
}
