#!/usr/bin/env python3
"""Check Alembic revision vs database schema."""

import sys

from sqlalchemy import create_engine, inspect, text

from apps.api.shared.migration_status import check_migration_version, get_alembic_head
from apps.api.shared.settings import get_settings


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    insp = inspect(engine)

    head = get_alembic_head()
    print(f"alembic head: {head}")

    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        print(f"alembic_version: {rev}")

        if rev != head:
            print(f"ERROR: database revision {rev!r} does not match code head {head!r}", file=sys.stderr)
            return 1

        for table in ("app_user", "recommendation_run"):
            indexes = [idx["name"] for idx in insp.get_indexes(table)]
            print(f"{table} indexes: {sorted(indexes)}")

    with engine.connect() as conn:
        from sqlalchemy.orm import Session

        with Session(bind=conn) as session:
            status = check_migration_version(session)
            print(f"migration check: {status}")
            if status.startswith("fail"):
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
