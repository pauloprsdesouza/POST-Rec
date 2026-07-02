import { formatApaInTextCitation, formatApaReference } from "@/shared/utils/apaCitation";
import type { EvidencePaper, Recommendation, SourceDocument, SotaAnchor } from "@/shared/types/api";

export const PAPER_REF_PATTERN = /(?<![A-Za-z0-9])[Pp](\d+)(?![A-Za-z0-9])/g;

export interface PaperRefEntry {
  paperId: string;
  title: string;
  url?: string;
  year?: number;
  authors?: string[];
  venue?: string;
  inEvidence: boolean;
}

export function normalizePaperId(value: string): string {
  const trimmed = value.trim().toUpperCase();
  return trimmed.startsWith("P") ? trimmed : `P${trimmed}`;
}

export function resolvePaperUrl(paper: { url?: string | null; doi?: string | null }): string | undefined {
  if (paper.url?.trim()) {
    return paper.url.trim();
  }
  const doi = paper.doi?.trim();
  if (!doi) {
    return undefined;
  }
  if (doi.startsWith("http://") || doi.startsWith("https://")) {
    return doi;
  }
  return `https://doi.org/${doi.replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")}`;
}

function upsertEntry(
  index: Map<string, PaperRefEntry>,
  paperId: string | undefined | null,
  partial: Omit<PaperRefEntry, "paperId" | "inEvidence">,
  inEvidence: boolean,
) {
  if (!paperId?.trim()) {
    return;
  }
  const normalized = normalizePaperId(paperId);
  const existing = index.get(normalized);
  index.set(normalized, {
    paperId: normalized,
    title: partial.title || existing?.title || normalized,
    url: partial.url ?? existing?.url,
    year: partial.year ?? existing?.year,
    authors: partial.authors?.length ? partial.authors : existing?.authors,
    venue: partial.venue ?? existing?.venue,
    inEvidence: inEvidence || (existing?.inEvidence ?? false),
  });
}

export function buildPaperRefIndex(
  recommendation: Recommendation,
  sources: SourceDocument[] = [],
): Map<string, PaperRefEntry> {
  const index = new Map<string, PaperRefEntry>();

  for (const [position, paper] of (recommendation.evidence_papers ?? []).entries()) {
    upsertEntry(
      index,
      paper.paper_id ?? `P${position + 1}`,
      {
        title: paper.title ?? paper.paper_id ?? `P${position + 1}`,
        url: resolvePaperUrl(paper),
        year: paper.year,
        authors: paper.authors,
        venue: paper.venue,
      },
      true,
    );
  }

  for (const anchor of recommendation.sota_anchors ?? []) {
    upsertEntry(
      index,
      anchor.paper_id,
      {
        title: anchor.title ?? anchor.paper_id ?? "",
        url: resolvePaperUrl(anchor),
        year: anchor.year,
      },
      false,
    );
  }

  const sourceByTitle = new Map(
    sources
      .filter((source) => source.title?.trim())
      .map((source) => [source.title!.toLowerCase().trim(), source]),
  );

  for (const [paperId, entry] of index) {
    const matchedSource = sourceByTitle.get(entry.title.toLowerCase().trim());
    if (!matchedSource) {
      continue;
    }
    upsertEntry(
      index,
      paperId,
      {
        title: entry.title,
        url: entry.url ?? resolvePaperUrl(matchedSource),
        year: entry.year ?? matchedSource.year,
        authors: entry.authors?.length ? entry.authors : matchedSource.authors,
        venue: entry.venue ?? matchedSource.venue,
      },
      entry.inEvidence,
    );
  }

  for (const source of sources) {
    if (!source.paper_id?.trim()) {
      continue;
    }
    upsertEntry(
      index,
      source.paper_id,
      {
        title: source.title ?? source.paper_id ?? "",
        url: resolvePaperUrl(source),
        year: source.year,
        authors: source.authors,
        venue: source.venue,
      },
      index.get(normalizePaperId(source.paper_id))?.inEvidence ?? false,
    );
  }

  return index;
}

export function formatPaperRefLabel(entry: PaperRefEntry): string {
  return formatApaInTextCitation({
    authors: entry.authors,
    year: entry.year,
    title: entry.title,
    venue: entry.venue,
  });
}

export function formatPaperRefTooltip(entry: PaperRefEntry): string {
  return formatApaReference(
    {
      authors: entry.authors,
      year: entry.year,
      title: entry.title,
      venue: entry.venue,
    },
    { maxLength: 500 },
  );
}

export type PaperRefTextPart =
  | { type: "text"; value: string }
  | { type: "ref"; value: string; paperId: string };

export function splitPaperRefText(text: string): PaperRefTextPart[] {
  const parts: PaperRefTextPart[] = [];
  let lastIndex = 0;
  const pattern = new RegExp(PAPER_REF_PATTERN.source, "g");

  for (const match of text.matchAll(pattern)) {
    const matchIndex = match.index ?? 0;
    if (matchIndex > lastIndex) {
      parts.push({ type: "text", value: text.slice(lastIndex, matchIndex) });
    }
    const paperId = normalizePaperId(match[1] ?? match[0]);
    parts.push({ type: "ref", value: match[0], paperId });
    lastIndex = matchIndex + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push({ type: "text", value: text.slice(lastIndex) });
  }

  return parts.length ? parts : [{ type: "text", value: text }];
}

export function paperHasRefContent(paper: EvidencePaper | SotaAnchor): boolean {
  return Boolean(paper.paper_id?.trim() || paper.title?.trim());
}
