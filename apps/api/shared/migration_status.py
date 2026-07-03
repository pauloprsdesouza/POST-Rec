"""Alembic revision helpers shared by health checks and ops scripts."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_alembic_head() -> str:
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    if not head:
        raise RuntimeError("Alembic has no head revision")
    return head


def get_db_revision(db: Session) -> str | None:
    return db.execute(text("SELECT version_num FROM alembic_version")).scalar()


def check_migration_version(db: Session) -> str:
    """Return a health-check style status string for migration alignment."""
    try:
        current = get_db_revision(db)
        if not current:
            return "fail: alembic_version table is empty"
        head = get_alembic_head()
        if current == head:
            return f"ok ({head})"
        return f"fail: db at {current}, code expects {head}"
    except Exception as exc:
        return f"fail: {exc}"
