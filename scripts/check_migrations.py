#!/usr/bin/env python3
"""Check Alembic revision vs database schema."""

from sqlalchemy import create_engine, inspect, text

from apps.api.shared.settings import get_settings


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    insp = inspect(engine)

    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        print(f"alembic_version: {rev}")

        for table in ("app_user", "recommendation_run"):
            indexes = [idx["name"] for idx in insp.get_indexes(table)]
            print(f"{table} indexes: {sorted(indexes)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
