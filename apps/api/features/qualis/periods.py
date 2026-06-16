"""Qualis evaluation period helpers."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.shared.database import SessionLocal
from apps.api.shared.models import QualisEvaluationPeriod

DEFAULT_PERIOD_LABEL = "2021-2024"


def parse_period_label(label: str) -> tuple[int, int]:
    """Parse a display label like '2021-2024' into (start_year, end_year)."""
    parts = label.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"invalid period label: {label!r}")
    start_year, end_year = int(parts[0]), int(parts[1])
    if start_year >= end_year:
        raise ValueError(f"invalid period range: {label!r}")
    return start_year, end_year


def format_period_label(start_year: int, end_year: int) -> str:
    return f"{start_year}-{end_year}"


def period_rank_from_label(period: str | None) -> int:
    """Higher rank means more recent; uses start_year when label is parseable."""
    if not period:
        return 0
    try:
        start_year, _ = parse_period_label(period)
        return start_year
    except ValueError:
        return 0


class PeriodResolver:
    """Resolve period labels to qualis_evaluation_period.id (cached per process)."""

    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory
        self._by_label: dict[str, int] = {}

    def _load(self, session: Session) -> None:
        if self._by_label:
            return
        rows = session.execute(
            select(
                QualisEvaluationPeriod.id,
                QualisEvaluationPeriod.label,
                QualisEvaluationPeriod.start_year,
                QualisEvaluationPeriod.end_year,
            )
        ).all()
        for period_id, label, start_year, end_year in rows:
            self._by_label[label] = period_id
            self._by_label[format_period_label(start_year, end_year)] = period_id

    def resolve_id(self, label: str) -> int:
        normalized = label.strip()
        cached = self._by_label.get(normalized)
        if cached is not None:
            return cached

        session = self._session_factory()
        try:
            self._load(session)
            period_id = self._by_label.get(normalized)
            if period_id is not None:
                return period_id

            start_year, end_year = parse_period_label(normalized)
            row = session.execute(
                select(QualisEvaluationPeriod.id).where(
                    QualisEvaluationPeriod.start_year == start_year,
                    QualisEvaluationPeriod.end_year == end_year,
                )
            ).scalar_one_or_none()
            if row is None:
                raise ValueError(f"unknown qualis evaluation period: {normalized!r}")
            self._by_label[normalized] = row
            self._by_label[format_period_label(start_year, end_year)] = row
            return row
        finally:
            session.close()

    def invalidate(self) -> None:
        self._by_label.clear()


@lru_cache
def get_period_resolver() -> PeriodResolver:
    return PeriodResolver()
