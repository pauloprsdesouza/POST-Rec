const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export const env = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
} as const;
