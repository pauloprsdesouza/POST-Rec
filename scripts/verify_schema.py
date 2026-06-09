#!/usr/bin/env python3
"""Verify database schema after migrations."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from apps.api.shared.database import engine

insp = inspect(engine)
tables = set(insp.get_table_names())

with engine.connect() as conn:
    version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    enums = conn.execute(
        text("SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname")
    ).scalars().all()

print(f"alembic_version: {version}")
print(f"enum_types: {', '.join(enums)}")
for name in ("study_session", "session_consent", "session_profile", "session_expectation"):
    print(f"  {name}: {'OK' if name in tables else 'MISSING'}")
for name in ("volunteer_session", "user_interaction_event", "audit_log", "exported_artifact"):
    print(f"  {name} removed: {name not in tables}")

if "recommendation_run" in tables:
    cols = {c["name"]: str(c["type"]) for c in insp.get_columns("recommendation_run")}
    print(f"recommendation_run.status type: {cols.get('status')}")
    print(f"recommendation_run.mode type: {cols.get('mode')}")

with engine.connect() as conn:
    udt_rows = conn.execute(
        text(
            """
            SELECT table_name, column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (
                (table_name = 'recommendation_run' AND column_name IN ('status', 'mode', 'current_step'))
                OR (table_name = 'study_session' AND column_name = 'status')
                OR (table_name = 'recommendation_candidate' AND column_name = 'status')
              )
            ORDER BY table_name, column_name
            """
        )
    ).all()
    print("postgres_udt_types:")
    for row in udt_rows:
        print(f"  {row.table_name}.{row.column_name} -> {row.udt_name}")
