/** Format seed topics for the multi-line textarea (one topic per line). */
export function formatSeedTopics(topics?: string[] | null): string {
  return (topics ?? []).join("\n");
}

/** Parse textarea content into seed topics; empty lines are ignored. */
export function parseSeedTopics(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((topic) => topic.trim())
    .filter(Boolean);
}

/** Apply parsed seed topics to recommendation defaults. */
export function withParsedSeedTopics<T extends { seed_topics?: string[] }>(
  defaults: T,
  text: string,
): T {
  return { ...defaults, seed_topics: parseSeedTopics(text) };
}
