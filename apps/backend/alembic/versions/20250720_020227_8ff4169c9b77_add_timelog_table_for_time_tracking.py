"""Add TimeLog table for time tracking

Revision ID: 8ff4169c9b77
Revises: 36c13bea2d03
Create Date: 2025-07-20 02:02:27.302370

Description:
    Creates the time_logs table for tracking time spent on tasks.
    This table allows users to log hours worked on specific tasks
    and provides data for analytics and reporting.

Safety Notes:
    - This migration creates a new table with no impact on existing data
    - Foreign keys reference existing users and tasks tables

Rollback Plan:
    - Simply drop the time_logs table to rollback
    - No data migration or transformation is involved
"""

from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = "8ff4169c9b77"
down_revision: Union[str, None] = "36c13bea2d03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Configure logging
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """
    Apply the migration.

    This function should be idempotent when possible.
    """
    logger.info(f"Applying migration {revision}")

    # Get database dialect for conditional operations
    connection = op.get_bind()
    dialect_name = connection.dialect.name

    try:
        # Create time_logs table
        op.create_table(
            "time_logs",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("task_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("hours", sa.Float(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

        # Create indexes for better query performance
        op.create_index("ix_time_logs_task_id", "time_logs", ["task_id"])
        op.create_index("ix_time_logs_user_id", "time_logs", ["user_id"])
        op.create_index("ix_time_logs_logged_at", "time_logs", ["logged_at"])

        logger.info(f"Successfully applied migration {revision}")
    except Exception as e:
        logger.error(f"Failed to apply migration {revision}: {str(e)}")
        raise


def downgrade() -> None:
    """
    Rollback the migration.

    This function should safely undo all changes made in upgrade().
    """
    logger.info(f"Rolling back migration {revision}")

    # Get database dialect for conditional operations
    connection = op.get_bind()
    dialect_name = connection.dialect.name

    try:
        # Drop indexes
        op.drop_index("ix_time_logs_logged_at", table_name="time_logs")
        op.drop_index("ix_time_logs_user_id", table_name="time_logs")
        op.drop_index("ix_time_logs_task_id", table_name="time_logs")

        # Drop time_logs table
        op.drop_table("time_logs")

        logger.info(f"Successfully rolled back migration {revision}")
    except Exception as e:
        logger.error(f"Failed to rollback migration {revision}: {str(e)}")
        raise


# Helper functions for common migration tasks
def create_index_if_not_exists(index_name: str, table_name: str, columns: list):
    """Create an index only if it doesn't already exist."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

    if index_name not in indexes:
        op.create_index(index_name, table_name, columns)
        logger.info(f"Created index {index_name} on {table_name}")
    else:
        logger.info(f"Index {index_name} already exists on {table_name}")


def drop_index_if_exists(index_name: str, table_name: str):
    """Drop an index only if it exists."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

    if index_name in indexes:
        op.drop_index(index_name, table_name)
        logger.info(f"Dropped index {index_name} from {table_name}")
    else:
        logger.info(f"Index {index_name} does not exist on {table_name}")


def add_column_if_not_exists(table_name: str, column: sa.Column):
    """Add a column only if it doesn't already exist."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns(table_name)]

    if column.name not in columns:
        op.add_column(table_name, column)
        logger.info(f"Added column {column.name} to {table_name}")
    else:
        logger.info(f"Column {column.name} already exists in {table_name}")


def drop_column_if_exists(table_name: str, column_name: str):
    """Drop a column only if it exists."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns(table_name)]

    if column_name in columns:
        op.drop_column(table_name, column_name)
        logger.info(f"Dropped column {column_name} from {table_name}")
    else:
        logger.info(f"Column {column_name} does not exist in {table_name}")
