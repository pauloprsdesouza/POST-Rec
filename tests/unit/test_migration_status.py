"""Migration version alignment tests."""

from pathlib import Path

from apps.api.shared.migration_status import get_alembic_head

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_head_is_defined():
    head = get_alembic_head()
    assert head
    revision_files = list((REPO_ROOT / "migrations" / "versions").glob(f"*{head}*.py"))
    assert revision_files, f"no migration file found for head revision {head!r}"
