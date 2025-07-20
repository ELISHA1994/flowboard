"""Add project management tables

Revision ID: 4d7525eb6be4
Revises: c2b8aa4f73dd
Create Date: 2025-07-19 15:46:57.245726

Description:
    Adds project management tables including projects, project_members, and project_invitations.
    Also adds project_id field to tasks table for project association.
    
Safety Notes:
    - This migration adds new tables and a nullable column to tasks
    - No data loss should occur
    
Rollback Plan:
    - Run alembic downgrade to remove the new tables and column
"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = '4d7525eb6be4'
down_revision: Union[str, None] = 'c2b8aa4f73dd'
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
        # Create projects table
        op.create_table('projects',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('owner_id', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create project_invitations table
        op.create_table('project_invitations',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('inviter_id', sa.String(), nullable=False),
            sa.Column('invitee_email', sa.String(length=320), nullable=False),
            sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='projectrole'), nullable=False),
            sa.Column('token', sa.String(), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['inviter_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token')
        )
        
        # Create project_members table
        op.create_table('project_members',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='projectrole'), nullable=False),
            sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_id', 'user_id', name='_project_user_uc')
        )
        
        # Add project_id to tasks table
        op.add_column('tasks', sa.Column('project_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
        
        # SQLite doesn't support adding foreign key constraints
        # We'll skip it for now since our models handle the relationship
        
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
        # Remove project_id from tasks table
        op.drop_index(op.f('ix_tasks_project_id'), table_name='tasks')
        op.drop_column('tasks', 'project_id')
        
        # Drop tables in reverse order
        op.drop_table('project_members')
        op.drop_table('project_invitations')
        op.drop_table('projects')
        
        # Drop the enum type if using PostgreSQL
        if dialect_name == 'postgresql':
            op.execute("DROP TYPE IF EXISTS projectrole")
        
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