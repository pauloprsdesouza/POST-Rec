import "bootstrap/dist/css/bootstrap.min.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { registerSW } from "virtual:pwa-register";

import App from "@/app/App";
import "@/shared/i18n";
import { syncPwaModeAttribute } from "@/shared/pwa/detect";
import { initTheme } from "@/shared/theme/themeStorage";
import "@/shared/styles/sign-in.scss";

initTheme();
syncPwaModeAttribute();

registerSW({ immediate: true });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
