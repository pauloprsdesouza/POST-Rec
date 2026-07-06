export const queryKeys = {
  runs: (accessToken: string | null, search?: string) =>
    ["runs", accessToken, search ?? ""] as const,
  runDetail: (accessToken: string | null, runId: string) =>
    ["run", accessToken, runId] as const,
  onboarding: (accessToken: string | null) => ["onboarding", accessToken] as const,
  validationDashboard: (accessToken: string | null) =>
    ["validation-dashboard", accessToken] as const,
  researchReport: (accessToken: string | null) => ["research-report", accessToken] as const,
  adminOverview: (accessToken: string | null) => ["admin-overview", accessToken] as const,
};
