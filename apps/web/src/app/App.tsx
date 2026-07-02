import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/context/AuthContext";
import { RunsProvider } from "@/features/runs/context/RunsContext";
import { CoachMarkProvider } from "@/shared/coachmarks/CoachMarkProvider";
import { env } from "@/shared/config/env";
import { ThemeProvider } from "@/shared/theme/ThemeContext";
import { AppRoutes } from "@/app/routes";

export default function App() {
  return (
    <BrowserRouter basename={env.basePath || "/"}>
      <ThemeProvider>
        <AuthProvider>
          <CoachMarkProvider>
            <RunsProvider>
              <AppRoutes />
            </RunsProvider>
          </CoachMarkProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
