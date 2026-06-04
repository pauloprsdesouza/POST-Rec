import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { ProtectedRoute } from "../components/routing/ProtectedRoute";
import { useAuth } from "../contexts/AuthContext";
import { ConsentPage } from "../pages/ConsentPage";
import { InsightsPage } from "../pages/InsightsPage";
import { NewRunPage } from "../pages/NewRunPage";
import { ProfilePage } from "../pages/ProfilePage";
import { RunDetailPage } from "../pages/RunDetailPage";
import { RecommendationsRedirect, RunsPage } from "../pages/RunsPage";
import { SignInPage } from "../pages/SignInPage";
import { SurveyPage } from "../pages/SurveyPage";
import { TransparencyPage } from "../pages/TransparencyPage";

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
  );
}
