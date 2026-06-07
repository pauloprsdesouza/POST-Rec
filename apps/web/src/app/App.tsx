import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/context/AuthContext";
import { RunsProvider } from "@/features/runs/context/RunsContext";
import { ThemeProvider } from "@/shared/theme/ThemeContext";
import { AppRoutes } from "@/app/routes";

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <RunsProvider>
            <AppRoutes />
          </RunsProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
