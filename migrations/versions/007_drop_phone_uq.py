"""Drop redundant phone_number unique constraint; uniqueness is on idx_app_user_phone_number."""

from alembic import op

revision = "007_drop_phone_uq"
down_revision = "006_repair_missing_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE app_user DROP CONSTRAINT IF EXISTS app_user_phone_number_key")


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'app_user'::regclass
                  AND conname = 'app_user_phone_number_key'
            ) THEN
                ALTER TABLE app_user ADD CONSTRAINT app_user_phone_number_key UNIQUE (phone_number);
            END IF;
        END $$;
        """
    )
