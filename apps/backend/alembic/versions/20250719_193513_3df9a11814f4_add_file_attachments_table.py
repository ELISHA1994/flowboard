"""Add file attachments table

Revision ID: 3df9a11814f4
Revises: add_comments_mentions
Create Date: 2025-07-19 19:35:13.819011

Description:
    Adds file_attachments table to support file uploads on tasks.
    Users can upload files to tasks they have access to.
    
Safety Notes:
    - Creates new table with foreign keys to tasks and users
    - No impact on existing data
    
Rollback Plan:
    - Drop the file_attachments table
    - Remove any uploaded files from disk storage
"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = '3df9a11814f4'
down_revision: Union[str, None] = 'add_comments_mentions'
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
        # Create file_attachments table
        op.create_table('file_attachments',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('task_id', sa.String(), nullable=False),
            sa.Column('uploaded_by_id', sa.String(), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=True),
            sa.Column('storage_path', sa.String(length=500), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index(op.f('ix_file_attachments_task_id'), 'file_attachments', ['task_id'], unique=False)
        op.create_index(op.f('ix_file_attachments_uploaded_by_id'), 'file_attachments', ['uploaded_by_id'], unique=False)
        
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
        op.drop_index(op.f('ix_file_attachments_uploaded_by_id'), table_name='file_attachments')
        op.drop_index(op.f('ix_file_attachments_task_id'), table_name='file_attachments')
        
        # Drop file_attachments table
        op.drop_table('file_attachments')
        
        logger.info(f"Successfully rolled back migration {revision}")
    except Exception as e:
        logger.error(f"Failed to rollback migration {revision}: {str(e)}")
        raise


# Helper functions for common migration tasks
def create_index_if_not_exists(index_name: str, table_name: str, columns: list):
    """Create an index only if it doesn't already exist."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    
    if index_name not in indexes:
        op.create_index(index_name, table_name, columns)
        logger.info(f"Created index {index_name} on {table_name}")
    else:
        logger.info(f"Index {index_name} already exists on {table_name}")


def drop_index_if_exists(index_name: str, table_name: str):
    """Drop an index only if it exists."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    
    if index_name in indexes:
        op.drop_index(index_name, table_name)
        logger.info(f"Dropped index {index_name} from {table_name}")
    else:
        logger.info(f"Index {index_name} does not exist on {table_name}")


def add_column_if_not_exists(table_name: str, column: sa.Column):
    """Add a column only if it doesn't already exist."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column.name not in columns:
        op.add_column(table_name, column)
        logger.info(f"Added column {column.name} to {table_name}")
    else:
        logger.info(f"Column {column.name} already exists in {table_name}")


def drop_column_if_exists(table_name: str, column_name: str):
    """Drop a column only if it exists."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name in columns:
        op.drop_column(table_name, column_name)
        logger.info(f"Dropped column {column_name} from {table_name}")
    else:
        logger.info(f"Column {column_name} does not exist in {table_name}")