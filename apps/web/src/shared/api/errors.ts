import { HttpError } from "./httpClient";

export function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof HttpError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}
