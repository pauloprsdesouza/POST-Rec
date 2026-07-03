"""Key OTP challenges by email instead of phone."""

from alembic import op
import sqlalchemy as sa

revision = "017_otp_email_challenges"
down_revision = "016_bootstrap_operator_admins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("auth_otp_challenge", sa.Column("email", sa.Text(), nullable=True))
    op.alter_column("auth_otp_challenge", "phone_number", existing_type=sa.Text(), nullable=True)
    op.create_index("idx_auth_otp_email_created", "auth_otp_challenge", ["email", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_auth_otp_email_created", table_name="auth_otp_challenge")
    op.alter_column("auth_otp_challenge", "phone_number", existing_type=sa.Text(), nullable=False)
    op.drop_column("auth_otp_challenge", "email")
