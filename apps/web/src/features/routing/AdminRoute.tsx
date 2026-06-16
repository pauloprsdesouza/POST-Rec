import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

interface AdminRouteProps {
  children: ReactNode;
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { isAuthenticated, isAdmin } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />;
  }
  if (!isAdmin) {
    return <Navigate to="/runs" replace />;
  }

  return children;
}
