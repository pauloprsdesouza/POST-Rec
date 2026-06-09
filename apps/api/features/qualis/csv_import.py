"""Parse Qualis Sucupira CSV exports for seeding and tests."""

from __future__ import annotations

import csv
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from apps.api.features.qualis.normalize import normalize_issn, normalize_title
from apps.api.features.qualis.periods import DEFAULT_PERIOD_LABEL
from apps.api.features.qualis.scoring import normalize_estrato


def csv_field(row: dict[str, str], *fragments: str) -> str | None:
    """Return a CSV cell whose header contains one of the given fragments."""
    for key, value in row.items():
        key_norm = unicodedata.normalize("NFKD", key.lstrip("\ufeff"))
        key_norm = "".join(ch for ch in key_norm if not unicodedata.combining(ch)).lower()
        if any(fragment.lower() in key_norm for fragment in fragments):
            return value
    return None


@dataclass(frozen=True, slots=True)
class QualisCsvRow:
    issn: str | None
    title: str
    title_normalized: str
    area: str
    estrato: str
    period: str


def detect_period_from_path(csv_path: Path | str, *, override: str | None = None) -> str:
    """Infer evaluation period from --period or filename (e.g. qualis_avaliacoes-2017-2020.csv)."""
    if override:
        return override.strip()
    match = re.search(r"(\d{4}-\d{4})", Path(csv_path).name)
    if match:
        return match.group(1)
    return DEFAULT_PERIOD_LABEL


def iter_qualis_csv_rows(csv_path: Path, *, period: str | None = None) -> Iterator[QualisCsvRow]:
    """Yield normalized rows from a Qualis CSV export, skipping invalid lines."""
    resolved_period = detect_period_from_path(csv_path, override=period)
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            estrato = normalize_estrato(csv_field(row, "estrato"))
            if not estrato:
                continue

            title_raw = (csv_field(row, "titulo", "título") or "").strip()
            area = (csv_field(row, "area", "área") or "").strip()
            if not title_raw or not area:
                continue

            title_normalized = normalize_title(title_raw)
            if not title_normalized:
                continue

            yield QualisCsvRow(
                issn=normalize_issn(csv_field(row, "issn")),
                title=title_raw,
                title_normalized=title_normalized,
                area=area,
                estrato=estrato,
                period=resolved_period,
            )
