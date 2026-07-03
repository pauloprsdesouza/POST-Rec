"""Migration version alignment tests."""

from apps.api.shared.migration_status import get_alembic_head


def test_alembic_head_is_defined():
    head = get_alembic_head()
    assert head
    assert head == "016_bootstrap_operator_admins"
