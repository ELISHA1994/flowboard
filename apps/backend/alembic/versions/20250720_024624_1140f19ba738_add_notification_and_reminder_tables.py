"""Add notification and reminder tables

Revision ID: 1140f19ba738
Revises: 62a2103fff54
Create Date: 2025-07-20 02:46:24.800848

Description:
    Creates tables for notification preferences, notifications, and task reminders.
    This enables the notification and reminder system for tasks.
    
Safety Notes:
    - This migration creates new tables with no impact on existing data
    - Foreign keys reference existing users and tasks tables
    
Rollback Plan:
    - Simply drop the new tables to rollback
    - No data migration or transformation is involved
"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision: str = '1140f19ba738'
down_revision: Union[str, None] = '62a2103fff54'
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
        # Create notification_preferences table
        op.create_table(
            'notification_preferences',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('notification_type', sa.String(50), nullable=False),
            sa.Column('channel', sa.String(20), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('frequency', sa.String(20), nullable=False, default='immediate'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'notification_type', 'channel', name='_user_notification_uc')
        )
        
        # Create indexes for notification_preferences
        op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
        
        # Create notifications table
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('type', sa.String(50), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('data', sa.Text(), nullable=True),
            sa.Column('read', sa.Boolean(), nullable=False, default=False),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for notifications
        op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'read'])
        op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
        
        # Create task_reminders table
        op.create_table(
            'task_reminders',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('task_id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('remind_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('reminder_type', sa.String(20), nullable=False, default='due_date'),
            sa.Column('offset_minutes', sa.Integer(), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('sent', sa.Boolean(), nullable=False, default=False),
            sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for task_reminders
        op.create_index('ix_task_reminders_remind_at', 'task_reminders', ['remind_at'])
        op.create_index('ix_task_reminders_sent', 'task_reminders', ['sent'])
        
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
        # Drop indexes from task_reminders
        op.drop_index('ix_task_reminders_sent', table_name='task_reminders')
        op.drop_index('ix_task_reminders_remind_at', table_name='task_reminders')
        
        # Drop task_reminders table
        op.drop_table('task_reminders')
        
        # Drop indexes from notifications
        op.drop_index('ix_notifications_created_at', table_name='notifications')
        op.drop_index('ix_notifications_user_read', table_name='notifications')
        
        # Drop notifications table
        op.drop_table('notifications')
        
        # Drop indexes from notification_preferences
        op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
        
        # Drop notification_preferences table
        op.drop_table('notification_preferences')
        
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