#!/usr/bin/env python3
"""Apply Alembic migrations and backfill tables missing from early revisions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from apps.api.shared.database import engine
from apps.api.shared.models import Base


def ensure_pgvector() -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()


def ensure_missing_tables() -> list[str]:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [table for table in Base.metadata.sorted_tables if table.name not in existing]
    if missing:
        Base.metadata.create_all(engine, tables=missing)
    return [table.name for table in missing]


def main() -> int:
    ensure_pgvector()
    alembic_cfg = Config(str(ROOT / "alembic.ini"))

    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        print(f"[migrate] alembic upgrade paused: {exc}")

    created = ensure_missing_tables()
    if created:
        print(f"[migrate] created missing tables: {', '.join(created)}")

    command.upgrade(alembic_cfg, "head")
    print("[migrate] database ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
