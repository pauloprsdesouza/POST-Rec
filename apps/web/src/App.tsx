import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "./contexts/AuthContext";
import { RunsProvider } from "./contexts/RunsContext";
import { AppRoutes } from "./routes/AppRoutes";

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
