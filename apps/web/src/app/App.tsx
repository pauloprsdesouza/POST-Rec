import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider } from "@/features/auth/context/AuthContext";
import { env } from "@/shared/config/env";
import { queryClient } from "@/shared/query/client";
import { ThemeProvider } from "@/shared/theme/ThemeContext";
import { AppRoutes } from "@/app/routes";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={env.basePath || "/"}>
        <ThemeProvider>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
