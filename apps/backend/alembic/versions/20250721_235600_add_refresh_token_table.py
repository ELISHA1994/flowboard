"""add_refresh_token_table

Revision ID: add_refresh_token
Revises: b397b78163be
Create Date: 2025-07-21 23:56:00.000000

Description:
    Adds refresh_tokens table for JWT authentication with rotation support.
    This enables long-lived sessions with secure token rotation and revocation.

Safety Notes:
    - This migration adds a new table with no impact on existing data
    - Includes proper indexes for performance
    - Foreign key to users table with CASCADE delete

Rollback Plan:
    - Simply run downgrade to drop the table
    - No data migration required
"""

from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_refresh_token"
down_revision: Union[str, None] = "b397b78163be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Configure logging
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """
    Apply the migration - create refresh_tokens table.
    """
    logger.info(f"Applying migration {revision}")

    # Check if table already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    if "refresh_tokens" in tables:
        logger.info("Table refresh_tokens already exists, skipping creation")
        return

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("family", sa.String(), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("browser", sa.String(length=100), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index("ix_refresh_tokens_family", "refresh_tokens", ["family"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_is_revoked", "refresh_tokens", ["is_revoked"])

    # Composite indexes for common queries
    op.create_index(
        "ix_refresh_tokens_user_not_revoked",
        "refresh_tokens",
        ["user_id", "is_revoked"],
    )
    op.create_index(
        "ix_refresh_tokens_family_not_revoked",
        "refresh_tokens",
        ["family", "is_revoked"],
    )
    op.create_index(
        "ix_refresh_tokens_expires_not_revoked",
        "refresh_tokens",
        ["expires_at", "is_revoked"],
    )

    logger.info(f"Successfully applied migration {revision}")


def downgrade() -> None:
    """
    Rollback the migration - drop refresh_tokens table.
    """
    logger.info(f"Rolling back migration {revision}")

    # Drop all indexes first
    op.drop_index("ix_refresh_tokens_expires_not_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_not_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_not_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_is_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_id", table_name="refresh_tokens")

    # Drop the table
    op.drop_table("refresh_tokens")

    logger.info(f"Successfully rolled back migration {revision}")
