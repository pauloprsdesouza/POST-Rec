import type { CoachMarkTour } from "./types";

export const COACH_MARK_TOURS: Record<string, CoachMarkTour> = {
  runsHome: {
    id: "runsHome",
    steps: [
      {
        target: "coach-runs-new-run",
        titleKey: "coachmarks.runsHome.newRun.title",
        bodyKey: "coachmarks.runsHome.newRun.body",
        placement: "top",
        align: "center",
        targetPreference: "first-visible",
        spotlightPadding: 8,
      },
      {
        target: "coach-runs-filters",
        titleKey: "coachmarks.runsHome.filters.title",
        bodyKey: "coachmarks.runsHome.filters.body",
        placement: "bottom",
        align: "start",
        spotlightPadding: 8,
      },
      {
        target: "coach-runs-ready",
        titleKey: "coachmarks.runsHome.ready.title",
        bodyKey: "coachmarks.runsHome.ready.body",
        placement: "top",
        align: "start",
        targetPreference: "largest",
        spotlightPadding: 12,
        skipIfHidden: true,
      },
      {
        target: "coach-bottom-nav",
        titleKey: "coachmarks.runsHome.mobileNav.title",
        bodyKey: "coachmarks.runsHome.mobileNav.body",
        placement: "top",
        align: "center",
        spotlightPadding: 6,
        skipIfHidden: true,
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
        placement: "bottom",
        align: "start",
        targetPreference: "largest",
        spotlightPadding: 12,
      },
      {
        target: "coach-newrun-mode",
        titleKey: "coachmarks.newRun.mode.title",
        bodyKey: "coachmarks.newRun.mode.body",
        placement: "bottom",
        align: "start",
        spotlightPadding: 8,
        skipIfHidden: true,
      },
      {
        target: "coach-newrun-submit",
        titleKey: "coachmarks.newRun.submit.title",
        bodyKey: "coachmarks.newRun.submit.body",
        placement: "top",
        align: "center",
        targetPreference: "first-visible",
        spotlightPadding: 8,
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
        placement: "bottom",
        align: "center",
        spotlightPadding: 10,
        skipIfHidden: true,
      },
      {
        target: "coach-run-rating",
        titleKey: "coachmarks.runReview.rating.title",
        bodyKey: "coachmarks.runReview.rating.body",
        placement: "top",
        align: "center",
        targetPreference: "largest",
        spotlightPadding: 12,
      },
      {
        target: "coach-run-sources",
        titleKey: "coachmarks.runReview.sources.title",
        bodyKey: "coachmarks.runReview.sources.body",
        placement: "top",
        align: "start",
        spotlightPadding: 8,
        skipIfHidden: true,
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
        placement: "bottom",
        align: "start",
        spotlightPadding: 8,
      },
      {
        target: "coach-profile-research-tab",
        titleKey: "coachmarks.profile.research.title",
        bodyKey: "coachmarks.profile.research.body",
        placement: "bottom",
        align: "start",
        spotlightPadding: 4,
      },
      {
        target: "coach-profile-preferences-tab",
        titleKey: "coachmarks.profile.preferences.title",
        bodyKey: "coachmarks.profile.preferences.body",
        placement: "bottom",
        align: "end",
        spotlightPadding: 4,
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
        placement: "bottom",
        align: "start",
        targetPreference: "largest",
        spotlightPadding: 14,
      },
    ],
  },
  projects: {
    id: "projects",
    steps: [
      {
        target: "coach-projects-header",
        titleKey: "coachmarks.projects.header.title",
        bodyKey: "coachmarks.projects.header.body",
        placement: "bottom",
        align: "start",
        spotlightPadding: 10,
      },
      {
        target: "coach-projects-list",
        titleKey: "coachmarks.projects.list.title",
        bodyKey: "coachmarks.projects.list.body",
        placement: "top",
        align: "start",
        targetPreference: "largest",
        spotlightPadding: 12,
        skipIfHidden: true,
      },
      {
        target: "coach-projects-phases",
        titleKey: "coachmarks.projects.phases.title",
        bodyKey: "coachmarks.projects.phases.body",
        placement: "bottom",
        align: "start",
        spotlightPadding: 10,
        skipIfHidden: true,
      },
      {
        target: "coach-projects-tasks",
        titleKey: "coachmarks.projects.tasks.title",
        bodyKey: "coachmarks.projects.tasks.body",
        placement: "top",
        align: "start",
        targetPreference: "largest",
        spotlightPadding: 12,
        skipIfHidden: true,
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
  if (pathname === "/insights" || pathname.startsWith("/admin/evaluation")) {
    return COACH_MARK_TOURS.insights;
  }
  if (pathname === "/projects") {
    return COACH_MARK_TOURS.projects;
  }
  if (/^\/projects\/[^/]+$/.test(pathname)) {
    return COACH_MARK_TOURS.projects;
  }
  return null;
}
