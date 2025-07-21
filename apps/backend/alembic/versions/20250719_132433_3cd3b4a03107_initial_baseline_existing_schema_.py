"""Initial baseline - existing schema snapshot

Revision ID: 3cd3b4a03107
Revises:
Create Date: 2025-07-19 13:24:33.385070

Description:
    This is the initial baseline migration that captures the existing database schema.
    It does not make any changes to the database structure.

    Existing tables:
    - users: User accounts with authentication
    - tasks: Task items with status, priority, dates, and time tracking
    - categories: Task categories with user association
    - tags: Task tags with color coding
    - task_categories: Many-to-many relationship between tasks and categories
    - task_tags: Many-to-many relationship between tasks and tags

Safety Notes:
    This migration is safe as it makes no schema changes.
    It simply establishes the baseline for future migrations.

Rollback Plan:
    This migration can be safely rolled back, which will remove the migration
    record from alembic_version table but will not affect the schema.
"""

from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = "3cd3b4a03107"
down_revision: Union[str, None] = None
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
        # This is a baseline migration - no schema changes needed
        # The database already has all tables created from manual migrations
        logger.info("Baseline migration - no schema changes applied")

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
        # This is a baseline migration - no schema changes to rollback
        logger.info("Baseline migration - no schema changes to rollback")

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
