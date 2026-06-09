import type { RunEvent } from "@/shared/types/api";

const TECHNICAL_LOG_PATTERN =
  /NoneType|AttributeError|RetryableFetchError|HTTPStatusError|object has no attribute|Traceback/i;

export function isTechnicalLogMessage(message: string | null | undefined): boolean {
  return Boolean(message?.trim() && TECHNICAL_LOG_PATTERN.test(message));
}

export function filterUserFacingEvents(events: RunEvent[]): RunEvent[] {
  return events.filter((event) => !isTechnicalLogMessage(event.message));
}
