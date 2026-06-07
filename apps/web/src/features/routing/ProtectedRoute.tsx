import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

interface ProtectedRouteProps {
  children: ReactNode;
  requireConsent?: boolean;
  requireProfile?: boolean;
}

export function ProtectedRoute({
  children,
  requireConsent = true,
  requireProfile = false,
}: ProtectedRouteProps) {
  const { isAuthenticated, consentDone, profileDone } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />;
  }
  if (requireConsent && !consentDone) {
    return <Navigate to="/consent" replace />;
  }
  if (requireProfile && !profileDone) {
    return <Navigate to="/profile" replace />;
  }

  return children;
}
