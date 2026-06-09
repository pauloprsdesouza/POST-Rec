"""PostgreSQL persistence for Qualis journal classifications."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from apps.api.features.qualis.csv_import import QualisCsvRow
from apps.api.features.qualis.periods import get_period_resolver
from apps.api.features.qualis.scoring import best_estrato, normalize_estrato
from apps.api.shared.database import SessionLocal
from apps.api.shared.models import QualisEvaluationPeriod, QualisJournal
from apps.api.shared.observability.logging import get_logger

logger = get_logger("postrec-qualis-repo")

BATCH_SIZE = 2_000


class QualisRepository:
    """Read path for Qualis lookups backed by qualis_journal."""

    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory
        self._available: bool | None = None
        self._row_count: int | None = None
        self._period_resolver = get_period_resolver()

    def _run(self, fn):
        session = self._session_factory()
        try:
            return fn(session)
        finally:
            session.close()

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:

            def _probe(session: Session) -> bool:
                return session.execute(text("SELECT 1 FROM qualis_journal LIMIT 1")).scalar() is not None

            self._available = bool(self._run(_probe))
        except Exception as exc:
            logger.warning("qualis_repository_unavailable", error=str(exc))
            self._available = False
        return self._available

    def row_count(self) -> int:
        if self._row_count is not None:
            return self._row_count

        def _count(session: Session) -> int:
            return int(session.scalar(select(func.count()).select_from(QualisJournal)) or 0)

        try:
            self._row_count = self._run(_count)
        except Exception:
            self._row_count = 0
        return self._row_count

    def row_count_by_period(self) -> dict[str, int]:
        def _count(session: Session) -> dict[str, int]:
            rows = session.execute(
                select(QualisEvaluationPeriod.label, func.count())
                .select_from(QualisJournal)
                .join(QualisEvaluationPeriod, QualisJournal.period_id == QualisEvaluationPeriod.id)
                .group_by(QualisEvaluationPeriod.label, QualisEvaluationPeriod.start_year)
                .order_by(QualisEvaluationPeriod.start_year)
            ).all()
            return {label: int(count) for label, count in rows}

        return self._run(_count)

    def lookup_classifications_by_issn(self, issn: str) -> list[tuple[str, str]]:
        def _query(session: Session) -> list[tuple[str, str]]:
            rows = session.execute(
                select(QualisJournal.estrato, QualisEvaluationPeriod.label)
                .join(QualisEvaluationPeriod, QualisJournal.period_id == QualisEvaluationPeriod.id)
                .where(QualisJournal.issn == issn)
                .order_by(QualisEvaluationPeriod.start_year.desc())
            ).all()
            return [(estrato, period_label) for estrato, period_label in rows if normalize_estrato(estrato)]

        return self._run(_query)

    def lookup_classifications_by_title(self, title_normalized: str) -> list[tuple[str, str]]:
        def _query(session: Session) -> list[tuple[str, str]]:
            rows = session.execute(
                select(QualisJournal.estrato, QualisEvaluationPeriod.label)
                .join(QualisEvaluationPeriod, QualisJournal.period_id == QualisEvaluationPeriod.id)
                .where(QualisJournal.title_normalized == title_normalized)
                .order_by(QualisEvaluationPeriod.start_year.desc())
            ).all()
            return [(estrato, period_label) for estrato, period_label in rows if normalize_estrato(estrato)]

        return self._run(_query)

    def truncate(self) -> None:
        def _truncate(session: Session) -> None:
            session.execute(text("TRUNCATE TABLE qualis_journal RESTART IDENTITY"))
            session.commit()

        self._run(_truncate)
        self._row_count = 0
        self._available = True

    def upsert_rows(self, rows: list[QualisCsvRow]) -> int:
        """Insert or update rows, keeping the highest estrato per (issn, area, period)."""
        deduped = _dedupe_by_issn_area_period(rows)
        if not deduped:
            return 0

        payload = [
            {
                "issn": row.issn,
                "title": row.title,
                "title_normalized": row.title_normalized,
                "area": row.area,
                "estrato": row.estrato,
                "period_id": self._period_resolver.resolve_id(row.period),
            }
            for row in deduped
        ]

        def _upsert(session: Session) -> None:
            stmt = insert(QualisJournal).values(payload)
            excluded = stmt.excluded
            upsert = stmt.on_conflict_do_update(
                index_elements=["issn", "area", "period_id"],
                index_where=text("issn IS NOT NULL"),
                set_={
                    "title": excluded.title,
                    "title_normalized": excluded.title_normalized,
                    "estrato": excluded.estrato,
                },
            )
            session.execute(upsert)
            session.commit()

        self._run(_upsert)
        self._row_count = None
        self._available = True
        return len(deduped)

    def import_csv_file(self, csv_path, *, truncate: bool = False, period: str | None = None) -> int:
        from pathlib import Path

        from apps.api.features.qualis.csv_import import iter_qualis_csv_rows

        path = Path(csv_path)
        if truncate:
            self.truncate()

        imported = 0
        batch: list[QualisCsvRow] = []
        for row in iter_qualis_csv_rows(path, period=period):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                imported += self._import_batch(batch)
                batch = []
        if batch:
            imported += self._import_batch(batch)
        return imported

    def _import_batch(self, rows: list[QualisCsvRow]) -> int:
        with_issn = [row for row in rows if row.issn]
        without_issn = [row for row in rows if not row.issn]
        count = 0
        if with_issn:
            count += self.upsert_rows(with_issn)
        if without_issn:
            count += self._insert_title_only(without_issn)
        return count

    def _insert_title_only(self, rows: list[QualisCsvRow]) -> int:
        payload = [
            {
                "issn": None,
                "title": row.title,
                "title_normalized": row.title_normalized,
                "area": row.area,
                "estrato": row.estrato,
                "period_id": self._period_resolver.resolve_id(row.period),
            }
            for row in rows
        ]

        def _insert(session: Session) -> None:
            session.execute(insert(QualisJournal).values(payload))
            session.commit()

        self._run(_insert)
        self._row_count = None
        return len(rows)


def _dedupe_by_issn_area_period(rows: list[QualisCsvRow]) -> list[QualisCsvRow]:
    merged: dict[tuple[str, str, str], QualisCsvRow] = {}
    for row in rows:
        if not row.issn:
            continue
        key = (row.issn, row.area, row.period)
        existing = merged.get(key)
        if existing is None:
            merged[key] = row
            continue
        best = best_estrato({existing.estrato, row.estrato})
        if best:
            merged[key] = QualisCsvRow(
                issn=row.issn,
                title=row.title,
                title_normalized=row.title_normalized,
                area=row.area,
                estrato=best,
                period=row.period,
            )
    return list(merged.values())


@lru_cache
def get_qualis_repository() -> QualisRepository:
    return QualisRepository()
