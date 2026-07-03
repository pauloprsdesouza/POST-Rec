import type { CoachMarkTourId } from "./types";

const STORAGE_KEY = "researchly.coachmarks";

interface CoachMarkStorage {
  completed: CoachMarkTourId[];
}

function readStorage(): CoachMarkStorage {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { completed: [] };
  }
  try {
    const parsed = JSON.parse(raw) as CoachMarkStorage;
    return { completed: Array.isArray(parsed.completed) ? parsed.completed : [] };
  } catch {
    return { completed: [] };
  }
}

function writeStorage(data: CoachMarkStorage): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function isTourCompleted(tourId: CoachMarkTourId): boolean {
  return readStorage().completed.includes(tourId);
}

export function markTourCompleted(tourId: CoachMarkTourId): void {
  const current = readStorage();
  if (current.completed.includes(tourId)) {
    return;
  }
  writeStorage({ completed: [...current.completed, tourId] });
}

export function resetCoachMarks(): void {
  localStorage.removeItem(STORAGE_KEY);
}
