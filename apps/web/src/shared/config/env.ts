const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
const basePath = (import.meta.env.VITE_BASE_PATH ?? "").replace(/\/$/, "");

export const env = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
  basePath,
} as const;
