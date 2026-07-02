export interface ApaCitationInput {
  authors?: string[] | null;
  year?: number | null;
  title?: string | null;
  venue?: string | null;
}

function parseDisplayName(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return "";
  }
  if (parts.length === 1) {
    return parts[0]!;
  }

  const last = parts[parts.length - 1]!;
  const initials = parts
    .slice(0, -1)
    .map((part) => `${part.replace(/\./g, "").charAt(0).toUpperCase()}.`)
    .join(" ");
  return `${last}, ${initials}`;
}

export function formatApaAuthorList(authors?: string[] | null): string | null {
  const cleaned = (authors ?? []).map((name) => name.trim()).filter(Boolean);
  if (!cleaned.length) {
    return null;
  }

  const formatted = cleaned.map(parseDisplayName).filter(Boolean);
  if (!formatted.length) {
    return null;
  }
  if (formatted.length === 1) {
    return formatted[0]!;
  }
  if (formatted.length === 2) {
    return `${formatted[0]} & ${formatted[1]}`;
  }
  return `${formatted.slice(0, -1).join(", ")}, & ${formatted[formatted.length - 1]}`;
}

function authorLastName(displayName: string): string {
  const parts = displayName.trim().split(/\s+/).filter(Boolean);
  return parts.length ? parts[parts.length - 1]! : displayName.trim();
}

function quotedTitleForInText(title?: string | null): string {
  const cleaned = (title?.trim() || "Untitled work").replace(/\.$/, "");
  if (cleaned.length <= 48) {
    return `"${cleaned}"`;
  }
  const words = cleaned.split(/\s+/);
  return `"${words.slice(0, 4).join(" ")}…"`;
}

export function formatApaInTextCitation(paper: ApaCitationInput): string {
  const year = paper.year ? String(paper.year) : "n.d.";
  const authors = (paper.authors ?? []).map((name) => name.trim()).filter(Boolean);

  if (!authors.length) {
    return `(${quotedTitleForInText(paper.title)}, ${year})`;
  }
  if (authors.length === 1) {
    return `(${authorLastName(authors[0]!)}, ${year})`;
  }
  if (authors.length === 2) {
    return `(${authorLastName(authors[0]!)} & ${authorLastName(authors[1]!)}, ${year})`;
  }
  return `(${authorLastName(authors[0]!)} et al., ${year})`;
}

function normalizeTitle(title: string): string {
  const trimmed = title.trim();
  if (!trimmed) {
    return "Untitled work";
  }
  return trimmed.endsWith(".") ? trimmed : `${trimmed}.`;
}

export function formatApaReference(
  paper: ApaCitationInput,
  options: { maxLength?: number } = {},
): string {
  const maxLength = options.maxLength ?? 140;
  const title = normalizeTitle(paper.title?.trim() || "Untitled work");
  const yearPart = paper.year ? `(${paper.year})` : "(n.d.)";
  const venue = paper.venue?.trim();
  const authors = formatApaAuthorList(paper.authors);

  let reference = authors
    ? `${authors} ${yearPart}. ${title}`
    : `${title} ${yearPart}`;

  if (venue) {
    reference = `${reference} ${venue.endsWith(".") ? venue : `${venue}.`}`;
  } else if (!reference.endsWith(".")) {
    reference = `${reference}.`;
  }

  if (reference.length <= maxLength) {
    return reference;
  }

  const prefix = authors ? `${authors} ${yearPart}. ` : `${title} ${yearPart}`;
  const remaining = maxLength - prefix.length - 1;
  if (remaining <= 10) {
    return `${reference.slice(0, maxLength - 1).trimEnd()}…`;
  }

  const titleBody = title.replace(/\.$/, "");
  const shortenedTitle = `${titleBody.slice(0, remaining).trimEnd()}…`;
  let shortened = authors ? `${authors} ${yearPart}. ${shortenedTitle}.` : `${shortenedTitle}. ${yearPart}.`;
  if (venue) {
    shortened = `${shortened} ${venue.endsWith(".") ? venue : `${venue}.`}`;
  }
  if (shortened.length > maxLength) {
    return `${shortened.slice(0, maxLength - 1).trimEnd()}…`;
  }
  return shortened;
}
