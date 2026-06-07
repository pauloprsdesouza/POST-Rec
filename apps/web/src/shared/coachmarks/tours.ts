import type { CoachMarkTour } from "./types";

export const COACH_MARK_TOURS: Record<string, CoachMarkTour> = {
  runsHome: {
    id: "runsHome",
    steps: [
      {
        target: "coach-runs-new-run",
        titleKey: "coachmarks.runsHome.newRun.title",
        bodyKey: "coachmarks.runsHome.newRun.body",
      },
      {
        target: "coach-runs-filters",
        titleKey: "coachmarks.runsHome.filters.title",
        bodyKey: "coachmarks.runsHome.filters.body",
      },
      {
        target: "coach-runs-ready",
        titleKey: "coachmarks.runsHome.ready.title",
        bodyKey: "coachmarks.runsHome.ready.body",
      },
      {
        target: "coach-bottom-nav",
        titleKey: "coachmarks.runsHome.mobileNav.title",
        bodyKey: "coachmarks.runsHome.mobileNav.body",
      },
    ],
  },
  newRun: {
    id: "newRun",
    steps: [
      {
        target: "coach-newrun-topics",
        titleKey: "coachmarks.newRun.topics.title",
        bodyKey: "coachmarks.newRun.topics.body",
      },
      {
        target: "coach-newrun-mode",
        titleKey: "coachmarks.newRun.mode.title",
        bodyKey: "coachmarks.newRun.mode.body",
      },
      {
        target: "coach-newrun-submit",
        titleKey: "coachmarks.newRun.submit.title",
        bodyKey: "coachmarks.newRun.submit.body",
      },
    ],
  },
  runReview: {
    id: "runReview",
    steps: [
      {
        target: "coach-run-carousel",
        titleKey: "coachmarks.runReview.carousel.title",
        bodyKey: "coachmarks.runReview.carousel.body",
      },
      {
        target: "coach-run-rating",
        titleKey: "coachmarks.runReview.rating.title",
        bodyKey: "coachmarks.runReview.rating.body",
      },
      {
        target: "coach-run-sources",
        titleKey: "coachmarks.runReview.sources.title",
        bodyKey: "coachmarks.runReview.sources.body",
      },
    ],
  },
  profile: {
    id: "profile",
    steps: [
      {
        target: "coach-profile-tabs",
        titleKey: "coachmarks.profile.tabs.title",
        bodyKey: "coachmarks.profile.tabs.body",
      },
      {
        target: "coach-profile-research-tab",
        titleKey: "coachmarks.profile.research.title",
        bodyKey: "coachmarks.profile.research.body",
      },
      {
        target: "coach-profile-preferences-tab",
        titleKey: "coachmarks.profile.preferences.title",
        bodyKey: "coachmarks.profile.preferences.body",
      },
    ],
  },
  insights: {
    id: "insights",
    steps: [
      {
        target: "coach-insights-overview",
        titleKey: "coachmarks.insights.overview.title",
        bodyKey: "coachmarks.insights.overview.body",
      },
    ],
  },
};

export function tourForPath(pathname: string): CoachMarkTour | null {
  if (pathname === "/runs") {
    return COACH_MARK_TOURS.runsHome;
  }
  if (pathname === "/runs/new") {
    return COACH_MARK_TOURS.newRun;
  }
  if (/^\/runs\/[^/]+$/.test(pathname) && pathname !== "/runs/new") {
    return COACH_MARK_TOURS.runReview;
  }
  if (pathname.startsWith("/profile")) {
    return COACH_MARK_TOURS.profile;
  }
  if (pathname === "/insights") {
    return COACH_MARK_TOURS.insights;
  }
  return null;
}
