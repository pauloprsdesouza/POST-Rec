import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/shared/layout/AppLayout";
import { ProtectedRoute } from "@/features/routing/ProtectedRoute";
import { useAuth } from "@/features/auth/context/AuthContext";

const SignInPage = lazy(() =>
  import("@/features/auth/pages/SignInPage").then((module) => ({ default: module.SignInPage })),
);
const ConsentPage = lazy(() =>
  import("@/features/consent/pages/ConsentPage").then((module) => ({ default: module.ConsentPage })),
);
const ProfilePage = lazy(() =>
  import("@/features/profile/pages/ProfilePage").then((module) => ({ default: module.ProfilePage })),
);
const NewRunPage = lazy(() =>
  import("@/features/runs/pages/NewRunPage").then((module) => ({ default: module.NewRunPage })),
);
const RunDetailPage = lazy(() =>
  import("@/features/runs/pages/RunDetailPage").then((module) => ({ default: module.RunDetailPage })),
);
const RunsPage = lazy(() =>
  import("@/features/runs/pages/RunsPage").then((module) => ({ default: module.RunsPage })),
);
const SurveyPage = lazy(() =>
  import("@/features/survey/pages/SurveyPage").then((module) => ({ default: module.SurveyPage })),
);
const TransparencyPage = lazy(() =>
  import("@/features/transparency/pages/TransparencyPage").then((module) => ({
    default: module.TransparencyPage,
  })),
);
const InsightsPage = lazy(() =>
  import("@/features/insights/pages/InsightsPage").then((module) => ({ default: module.InsightsPage })),
);

const RecommendationsRedirect = lazy(() =>
  import("@/features/runs/pages/RunsPage").then((module) => ({
    default: module.RecommendationsRedirect,
  })),
);

function RouteFallback() {
  return (
    <div className="route-loading" aria-live="polite">
      Loading…
    </div>
  );
}

function HomeRedirect() {
  const { isAuthenticated, consentDone, profileDone } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />;
  }
  if (!consentDone) {
    return <Navigate to="/consent" replace />;
  }
  if (!profileDone) {
    return <Navigate to="/profile" replace />;
  }
  return <Navigate to="/runs" replace />;
}

export function AppRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/sign-in" element={<SignInPage />} />
        <Route
          element={
            <ProtectedRoute requireConsent={false} requireProfile={false}>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/consent" element={<ConsentPage />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute requireConsent requireProfile={false}>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs/new"
            element={
              <ProtectedRoute requireConsent requireProfile>
                <NewRunPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs/:runId"
            element={
              <ProtectedRoute requireConsent requireProfile>
                <RunDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs"
            element={
              <ProtectedRoute requireConsent requireProfile>
                <RunsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/recommendations" element={<RecommendationsRedirect />} />
          <Route path="/my-runs" element={<Navigate to="/runs" replace />} />
          <Route
            path="/survey"
            element={
              <ProtectedRoute requireConsent requireProfile>
                <SurveyPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/how-it-works"
            element={
              <ProtectedRoute requireConsent requireProfile={false}>
                <TransparencyPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/insights"
            element={
              <ProtectedRoute requireConsent requireProfile>
                <InsightsPage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
