"""Add subtasks and task dependencies

Revision ID: c2b8aa4f73dd
Revises: 3cd3b4a03107
Create Date: 2025-07-19 13:55:17.471508

Description:
    This migration adds support for subtasks and task dependencies:
    - Adds parent_task_id column to tasks table for subtask relationships
    - Creates task_dependencies table for managing task dependencies
    - Adds necessary indexes and foreign key constraints

Safety Notes:
    - This migration adds new columns and tables without modifying existing data
    - All new columns are nullable to ensure backward compatibility

Rollback Plan:
    - The migration can be safely rolled back
    - It will drop the new table and column without affecting existing data
"""

from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = "c2b8aa4f73dd"
down_revision: Union[str, None] = "3cd3b4a03107"
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
        # Create task_dependencies table
        op.create_table(
            "task_dependencies",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("task_id", sa.String(), nullable=False),
            sa.Column("depends_on_id", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["depends_on_id"],
                ["tasks.id"],
            ),
            sa.ForeignKeyConstraint(
                ["task_id"],
                ["tasks.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("task_id", "depends_on_id", name="_task_dependency_uc"),
        )

        # Create indexes for task_dependencies
        op.create_index(
            op.f("ix_task_dependencies_depends_on_id"),
            "task_dependencies",
            ["depends_on_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_task_dependencies_id"), "task_dependencies", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_task_dependencies_task_id"),
            "task_dependencies",
            ["task_id"],
            unique=False,
        )

        # Add parent_task_id column to tasks table
        op.add_column("tasks", sa.Column("parent_task_id", sa.String(), nullable=True))

        # Create index for parent_task_id
        op.create_index(
            op.f("ix_tasks_parent_task_id"), "tasks", ["parent_task_id"], unique=False
        )

        # Add foreign key constraint for self-referential relationship (skip for SQLite)
        if dialect_name != "sqlite":
            op.create_foreign_key(
                "fk_tasks_parent_task_id", "tasks", "tasks", ["parent_task_id"], ["id"]
            )

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
        # Drop foreign key constraint (skip for SQLite)
        if dialect_name != "sqlite":
            op.drop_constraint("fk_tasks_parent_task_id", "tasks", type_="foreignkey")

        # Drop index on parent_task_id
        op.drop_index(op.f("ix_tasks_parent_task_id"), table_name="tasks")

        # Drop parent_task_id column
        op.drop_column("tasks", "parent_task_id")

        # Drop indexes on task_dependencies
        op.drop_index(
            op.f("ix_task_dependencies_task_id"), table_name="task_dependencies"
        )
        op.drop_index(op.f("ix_task_dependencies_id"), table_name="task_dependencies")
        op.drop_index(
            op.f("ix_task_dependencies_depends_on_id"), table_name="task_dependencies"
        )

        # Drop task_dependencies table
        op.drop_table("task_dependencies")

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
