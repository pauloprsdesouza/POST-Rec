#!/usr/bin/env python3

"""Import Qualis Sucupira CSV into PostgreSQL and optionally warm Redis cache."""



from __future__ import annotations



import argparse

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))



from sqlalchemy import select



from apps.api.features.qualis.cache import QualisCache, QualisCacheKeys

from apps.api.features.qualis.csv_import import detect_period_from_path, iter_qualis_csv_rows

from apps.api.features.qualis.repository import QualisRepository, get_qualis_repository

from apps.api.features.qualis.scoring import resolve_qualis_classification

from apps.api.shared.database import init_db

from apps.api.shared.models import QualisEvaluationPeriod, QualisJournal

from apps.api.shared.settings import get_settings





def _resolve_csv_path(raw: str | None) -> Path:

    configured = (raw or get_settings().qualis_csv_path or "qualis_avaliacoes-2021-2024.csv").strip()

    path = Path(configured)

    if not path.is_absolute():

        path = ROOT / path

    return path





def _default_csv_paths() -> list[Path]:

    candidates = [

        ROOT / "qualis_avaliacoes-2021-2024.csv",

        ROOT / "qualis_avaliacoes-2017-2020.csv",

        ROOT / "qualis_avaliacoes.csv",

    ]

    return [path for path in candidates if path.is_file()]





def _warm_cache(repo: QualisRepository, cache: QualisCache) -> int:

    from apps.api.shared.database import SessionLocal



    session = SessionLocal()

    warmed = 0

    try:

        issn_rows = session.execute(
            select(QualisJournal.issn, QualisJournal.estrato, QualisEvaluationPeriod.label)
            .join(QualisEvaluationPeriod, QualisJournal.period_id == QualisEvaluationPeriod.id)
            .where(QualisJournal.issn.is_not(None))
        ).all()

        issn_map: dict[str, list[tuple[str, str]]] = {}

        for issn, estrato, period in issn_rows:

            if issn:

                issn_map.setdefault(issn, []).append((estrato, period))



        title_rows = session.execute(
            select(
                QualisJournal.title_normalized,
                QualisJournal.estrato,
                QualisEvaluationPeriod.label,
            ).join(QualisEvaluationPeriod, QualisJournal.period_id == QualisEvaluationPeriod.id)
        ).all()

        title_map: dict[str, list[tuple[str, str]]] = {}

        for title_normalized, estrato, period in title_rows:

            title_map.setdefault(title_normalized, []).append((estrato, period))



        entries: dict[str, dict] = {}

        for issn, classifications in issn_map.items():

            estrato, period = resolve_qualis_classification(classifications)

            entries[QualisCacheKeys.issn(issn)] = {"estrato": estrato, "period": period}

        for title, classifications in title_map.items():

            estrato, period = resolve_qualis_classification(classifications)

            entries[QualisCacheKeys.title(title)] = {"estrato": estrato, "period": period}



        batch: dict[str, dict] = {}

        for key, value in entries.items():

            batch[key] = value

            if len(batch) >= 500:

                cache.set_many(batch)

                warmed += len(batch)

                batch = {}

        if batch:

            cache.set_many(batch)

            warmed += len(batch)

    finally:

        session.close()

    return warmed





def _seed_csv(repo: QualisRepository, csv_path: Path, *, period: str | None, truncate: bool) -> None:

    resolved_period = detect_period_from_path(csv_path, override=period)

    csv_rows = sum(1 for _ in iter_qualis_csv_rows(csv_path, period=resolved_period))

    imported = repo.import_csv_file(csv_path, truncate=truncate, period=resolved_period)

    print(f"CSV: {csv_path.name} (period={resolved_period})")

    print(f"  valid rows: {csv_rows}")

    print(f"  imported batch rows processed: {imported}")





def main() -> int:

    parser = argparse.ArgumentParser(description="Seed qualis_journal from CAPES Sucupira CSV.")

    parser.add_argument("--csv", dest="csv_path", default=None, help="Path to a Qualis CSV export")

    parser.add_argument(

        "--period",

        default=None,

        help="Evaluation period label (e.g. 2021-2024). Auto-detected from filename when omitted.",

    )

    parser.add_argument(

        "--all-periods",

        action="store_true",

        help="Import all known period CSV files from the repo root.",

    )

    parser.add_argument(

        "--truncate",

        action="store_true",

        help="Truncate qualis_journal before import (full reload).",

    )

    parser.add_argument(

        "--warm-cache",

        action="store_true",

        help="Populate Redis qualis:* keys after import (pipelined).",

    )

    parser.add_argument(

        "--migrate",

        action="store_true",

        help="Run alembic upgrade head before seeding.",

    )

    args = parser.parse_args()



    if args.migrate:

        init_db()



    repo = get_qualis_repository()

    if args.truncate:

        repo.truncate()

        print("Truncated qualis_journal")



    if args.all_periods:

        csv_paths = _default_csv_paths()

        if not csv_paths:

            print("No Qualis CSV files found in repo root.", file=sys.stderr)

            return 1

        for csv_path in csv_paths:

            _seed_csv(repo, csv_path, period=args.period, truncate=False)

    else:

        csv_path = _resolve_csv_path(args.csv_path)

        if not csv_path.is_file():

            print(f"CSV not found: {csv_path}", file=sys.stderr)

            return 1

        _seed_csv(repo, csv_path, period=args.period, truncate=False)



    row_count = repo.row_count()

    print(f"qualis_journal row count: {row_count}")

    for period, count in sorted(repo.row_count_by_period().items()):

        print(f"  {period}: {count}")



    if args.warm_cache:

        cache = QualisCache()

        if not cache.enabled:

            print("Redis cache unavailable — skipped warm-cache", file=sys.stderr)

        else:

            cache.invalidate_all()

            warmed = _warm_cache(repo, cache)

            print(f"Redis keys warmed: {warmed}")



    return 0





if __name__ == "__main__":

    raise SystemExit(main())

