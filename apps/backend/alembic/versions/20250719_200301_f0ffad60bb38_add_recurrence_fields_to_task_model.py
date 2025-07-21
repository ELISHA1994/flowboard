"""Add recurrence fields to Task model

Revision ID: f0ffad60bb38
Revises: 3df9a11814f4
Create Date: 2025-07-19 20:03:01.434883

Description:
    Adds support for recurring tasks by adding recurrence pattern fields to the Task model.
    This includes:
    - is_recurring: Boolean flag to indicate if a task recurs
    - recurrence_pattern: Enum for recurrence patterns (daily, weekly, monthly, yearly, weekdays, custom)
    - recurrence_interval: Interval for the pattern (e.g., every 2 days)
    - recurrence_days_of_week: For weekly patterns
    - recurrence_day_of_month: For monthly patterns
    - recurrence_month_of_year: For yearly patterns
    - recurrence_end_date: When recurrence should stop
    - recurrence_count: Number of occurrences
    - recurrence_parent_id: Link to original recurring task

Safety Notes:
    - This migration adds columns only, no data is modified
    - All new columns are nullable or have defaults
    - Safe to run on production

Rollback Plan:
    - Run downgrade to remove the added columns
    - No data loss will occur as columns are new
"""

from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite
import enum


class RecurrencePattern(str, enum.Enum):
    """Recurrence pattern enumeration"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKDAYS = "weekdays"
    CUSTOM = "custom"


# revision identifiers, used by Alembic.
revision: str = "f0ffad60bb38"
down_revision: Union[str, None] = "3df9a11814f4"
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
        # Add recurrence fields to tasks table
        add_column_if_not_exists(
            "tasks",
            sa.Column(
                "is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
        )
        add_column_if_not_exists(
            "tasks",
            sa.Column("recurrence_pattern", sa.Enum(RecurrencePattern), nullable=True),
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_interval", sa.Integer(), nullable=True)
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_days_of_week", sa.String(20), nullable=True)
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_day_of_month", sa.Integer(), nullable=True)
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_month_of_year", sa.Integer(), nullable=True)
        )
        add_column_if_not_exists(
            "tasks",
            sa.Column("recurrence_end_date", sa.DateTime(timezone=True), nullable=True),
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_count", sa.Integer(), nullable=True)
        )
        add_column_if_not_exists(
            "tasks", sa.Column("recurrence_parent_id", sa.String(), nullable=True)
        )

        # Add foreign key constraint for recurrence_parent_id
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.create_foreign_key(
                "fk_tasks_recurrence_parent_id",
                "tasks",
                ["recurrence_parent_id"],
                ["id"],
                ondelete="SET NULL",
            )

        # Add index for recurrence queries
        create_index_if_not_exists(
            "ix_tasks_recurrence_parent_id", "tasks", ["recurrence_parent_id"]
        )
        create_index_if_not_exists("ix_tasks_is_recurring", "tasks", ["is_recurring"])

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
        drop_index_if_exists("ix_tasks_is_recurring", "tasks")
        drop_index_if_exists("ix_tasks_recurrence_parent_id", "tasks")

        # Drop foreign key constraint
        with op.batch_alter_table("tasks") as batch_op:
            try:
                batch_op.drop_constraint(
                    "fk_tasks_recurrence_parent_id", type_="foreignkey"
                )
            except Exception as e:
                logger.warning(f"Could not drop foreign key constraint: {e}")

        # Remove recurrence columns
        drop_column_if_exists("tasks", "recurrence_parent_id")
        drop_column_if_exists("tasks", "recurrence_count")
        drop_column_if_exists("tasks", "recurrence_end_date")
        drop_column_if_exists("tasks", "recurrence_month_of_year")
        drop_column_if_exists("tasks", "recurrence_day_of_month")
        drop_column_if_exists("tasks", "recurrence_days_of_week")
        drop_column_if_exists("tasks", "recurrence_interval")
        drop_column_if_exists("tasks", "recurrence_pattern")
        drop_column_if_exists("tasks", "is_recurring")

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
