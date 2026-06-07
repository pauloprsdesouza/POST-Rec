import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/context/AuthContext";
import { RunsProvider } from "@/features/runs/context/RunsContext";
import { AppRoutes } from "@/app/routes";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RunsProvider>
          <AppRoutes />
        </RunsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
