import type { RecommendationRun } from "@/shared/types/api";

const TOKEN_RE = /[\w\u00c0-\u024f]+/gu;
const MIN_TOKEN_LEN = 2;

function normalizeTokens(query: string): string[] {
  const matches = query.match(TOKEN_RE) ?? [];
  return matches.map((token) => token.toLowerCase()).filter((token) => token.length >= MIN_TOKEN_LEN);
}

function runSearchText(run: RecommendationRun): string {
  return [
    run.topics?.join(" "),
    run.mode,
    run.status,
    run.current_step,
    run.search_snippet,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function filterRunsLocally(runs: RecommendationRun[], query: string): RecommendationRun[] {
  const tokens = normalizeTokens(query.trim());
  if (tokens.length === 0) {
    return runs;
  }

  return runs.filter((run) => {
    const haystack = runSearchText(run);
    return tokens.every((token) => haystack.includes(token));
  });
}

export const LOCAL_SEARCH_RUN_LIMIT = 100;
