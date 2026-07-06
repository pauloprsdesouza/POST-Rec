import { lazy, Suspense } from "react";

import "@/shared/styles/authenticated.scss";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { useTranslation } from "react-i18next";

const AppLayout = lazy(() =>
  import("@/shared/layout/AppLayout").then((module) => ({ default: module.AppLayout })),
);
const CoachMarkProvider = lazy(() =>
  import("@/shared/coachmarks/CoachMarkProvider").then((module) => ({
    default: module.CoachMarkProvider,
  })),
);
const RunsProvider = lazy(() =>
  import("@/features/runs/context/RunsContext").then((module) => ({
    default: module.RunsProvider,
  })),
);

function ShellFallback() {
  const { t } = useTranslation();
  return (
    <div className="route-loading" aria-live="polite">
      <LoadingSpinner label={t("common.loading")} />
    </div>
  );
}

export function AuthenticatedShell() {
  return (
    <Suspense fallback={<ShellFallback />}>
      <CoachMarkProvider>
        <RunsProvider>
          <AppLayout />
        </RunsProvider>
      </CoachMarkProvider>
    </Suspense>
  );
}
