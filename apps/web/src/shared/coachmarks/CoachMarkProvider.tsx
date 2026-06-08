import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { CoachMarkOverlay } from "./CoachMarkOverlay";
import { resolveTourSteps } from "./steps";
import { isTourCompleted, markTourCompleted, resetCoachMarks } from "./storage";
import { COACH_MARK_TOURS, tourForPath } from "./tours";
import type { CoachMarkStep, CoachMarkTourId } from "./types";

interface CoachMarkContextValue {
  activeTourId: CoachMarkTourId | null;
  startTour: (tourId: CoachMarkTourId) => void;
  startTourForCurrentPage: () => void;
  resetTours: () => void;
}

const CoachMarkContext = createContext<CoachMarkContextValue | undefined>(undefined);

const AUTO_START_DELAY_MS = 700;

export function CoachMarkProvider({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const { profileDone, consentDone } = useAuth();
  const [activeTourId, setActiveTourId] = useState<CoachMarkTourId | null>(null);
  const [activeSteps, setActiveSteps] = useState<CoachMarkStep[]>([]);
  const [stepIndex, setStepIndex] = useState(0);

  const closeTour = useCallback((tourId: CoachMarkTourId, completed: boolean) => {
    if (completed) {
      markTourCompleted(tourId);
    }
    setActiveTourId(null);
    setActiveSteps([]);
    setStepIndex(0);
  }, []);

  const startTour = useCallback((tourId: CoachMarkTourId) => {
    const tour = COACH_MARK_TOURS[tourId];
    if (!tour) {
      return;
    }

    const steps = resolveTourSteps(tour.steps);
    if (!steps.length) {
      markTourCompleted(tourId);
      return;
    }

    setActiveTourId(tourId);
    setActiveSteps(steps);
    setStepIndex(0);
  }, []);

  const startTourForCurrentPage = useCallback(() => {
    const tour = tourForPath(pathname);
    if (tour) {
      startTour(tour.id);
    }
  }, [pathname, startTour]);

  const resetTours = useCallback(() => {
    resetCoachMarks();
    setActiveTourId(null);
    setActiveSteps([]);
    setStepIndex(0);
  }, []);

  useEffect(() => {
    if (!profileDone || !consentDone || activeTourId) {
      return;
    }

    const tour = tourForPath(pathname);
    if (!tour || isTourCompleted(tour.id)) {
      return;
    }

    const timer = window.setTimeout(() => {
      startTour(tour.id);
    }, AUTO_START_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [activeTourId, consentDone, pathname, profileDone, startTour]);

  const handleNext = useCallback(() => {
    if (!activeTourId || !activeSteps.length) {
      return;
    }
    if (stepIndex >= activeSteps.length - 1) {
      closeTour(activeTourId, true);
      return;
    }
    setStepIndex((current) => current + 1);
  }, [activeSteps.length, activeTourId, closeTour, stepIndex]);

  const handleBack = useCallback(() => {
    setStepIndex((current) => Math.max(current - 1, 0));
  }, []);

  const handleSkip = useCallback(() => {
    if (activeTourId) {
      closeTour(activeTourId, true);
    }
  }, [activeTourId, closeTour]);

  const value = useMemo(
    () => ({
      activeTourId,
      startTour,
      startTourForCurrentPage,
      resetTours,
    }),
    [activeTourId, resetTours, startTour, startTourForCurrentPage],
  );

  return (
    <CoachMarkContext.Provider value={value}>
      {children}
      {activeTourId && activeSteps.length > 0 ? (
        <CoachMarkOverlay
          tourId={activeTourId}
          steps={activeSteps}
          stepIndex={stepIndex}
          onNext={handleNext}
          onBack={handleBack}
          onSkip={handleSkip}
        />
      ) : null}
    </CoachMarkContext.Provider>
  );
}

export function useCoachMarks(): CoachMarkContextValue {
  const context = useContext(CoachMarkContext);
  if (!context) {
    throw new Error("useCoachMarks must be used within CoachMarkProvider");
  }
  return context;
}
