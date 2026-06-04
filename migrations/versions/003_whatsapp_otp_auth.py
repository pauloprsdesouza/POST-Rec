"""Passwordless WhatsApp OTP auth and notifications."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_whatsapp_otp_auth"
down_revision = "002_user_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("phone_number", sa.Text(), nullable=True))
    op.add_column(
        "app_user",
        sa.Column("whatsapp_opt_in", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.alter_column("app_user", "email", existing_type=sa.Text(), nullable=True)
    op.alter_column("app_user", "password_hash", existing_type=sa.Text(), nullable=True)
    op.create_index("idx_app_user_phone_number", "app_user", ["phone_number"], unique=True)

    op.create_table(
        "auth_otp_challenge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False, server_default="login"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_auth_otp_phone_created",
        "auth_otp_challenge",
        ["phone_number", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_auth_otp_phone_created", table_name="auth_otp_challenge")
    op.drop_table("auth_otp_challenge")
    op.drop_index("idx_app_user_phone_number", table_name="app_user")
    op.alter_column("app_user", "password_hash", existing_type=sa.Text(), nullable=False)
    op.alter_column("app_user", "email", existing_type=sa.Text(), nullable=False)
    op.drop_column("app_user", "whatsapp_opt_in")
    op.drop_column("app_user", "phone_number")
