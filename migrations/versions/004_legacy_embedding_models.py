"""Normalize legacy embedding model names stored in the database."""

from alembic import op

revision = "004_legacy_embedding_models"
down_revision = "003_whatsapp_otp_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE document_embedding
        SET embedding_model = 'gemini-embedding-001'
        WHERE embedding_model LIKE 'text-embedding-%'
           OR embedding_model = 'models/text-embedding-004'
        """
    )


def downgrade() -> None:
    pass
