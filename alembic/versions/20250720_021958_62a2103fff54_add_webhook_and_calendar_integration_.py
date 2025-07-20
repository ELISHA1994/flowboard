"""Add webhook and calendar integration tables

Revision ID: 62a2103fff54
Revises: 8ff4169c9b77
Create Date: 2025-07-20 02:19:58.806221

Description:
    Creates tables for webhook subscriptions, webhook deliveries,
    calendar integrations, and task-calendar sync mappings.
    This enables external integrations with webhooks and calendar services.
    
Safety Notes:
    - This migration creates new tables with no impact on existing data
    - Foreign keys reference existing users, tasks, and projects tables
    
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
revision: str = '62a2103fff54'
down_revision: Union[str, None] = '8ff4169c9b77'
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
        # Create webhook_subscriptions table
        op.create_table(
            'webhook_subscriptions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('url', sa.String(500), nullable=False),
            sa.Column('secret', sa.String(255), nullable=True),
            sa.Column('events', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('project_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for webhook_subscriptions
        op.create_index('ix_webhook_subscriptions_user_id', 'webhook_subscriptions', ['user_id'])
        op.create_index('ix_webhook_subscriptions_project_id', 'webhook_subscriptions', ['project_id'])
        
        # Create webhook_deliveries table
        op.create_table(
            'webhook_deliveries',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('subscription_id', sa.String(), nullable=False),
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('payload', sa.Text(), nullable=False),
            sa.Column('status_code', sa.Integer(), nullable=True),
            sa.Column('response', sa.Text(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
            sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for webhook_deliveries
        op.create_index('ix_webhook_deliveries_subscription_id', 'webhook_deliveries', ['subscription_id'])
        op.create_index('ix_webhook_deliveries_delivered_at', 'webhook_deliveries', ['delivered_at'])
        
        # Create calendar_integrations table
        op.create_table(
            'calendar_integrations',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('provider', sa.String(20), nullable=False),
            sa.Column('calendar_id', sa.String(255), nullable=False),
            sa.Column('calendar_name', sa.String(255), nullable=True),
            sa.Column('access_token', sa.Text(), nullable=False),
            sa.Column('refresh_token', sa.Text(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sync_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sync_direction', sa.String(20), nullable=False, default='both'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for calendar_integrations
        op.create_index('ix_calendar_integrations_user_id', 'calendar_integrations', ['user_id'])
        op.create_index('ix_calendar_integrations_provider', 'calendar_integrations', ['provider'])
        
        # Create task_calendar_sync table
        op.create_table(
            'task_calendar_sync',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('task_id', sa.String(), nullable=False),
            sa.Column('calendar_integration_id', sa.String(), nullable=False),
            sa.Column('calendar_event_id', sa.String(255), nullable=False),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['calendar_integration_id'], ['calendar_integrations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('task_id', 'calendar_integration_id', name='_task_calendar_uc')
        )
        
        # Create indexes for task_calendar_sync
        op.create_index('ix_task_calendar_sync_task_id', 'task_calendar_sync', ['task_id'])
        op.create_index('ix_task_calendar_sync_calendar_integration_id', 'task_calendar_sync', ['calendar_integration_id'])
        
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
        # Drop indexes from task_calendar_sync
        op.drop_index('ix_task_calendar_sync_calendar_integration_id', table_name='task_calendar_sync')
        op.drop_index('ix_task_calendar_sync_task_id', table_name='task_calendar_sync')
        
        # Drop task_calendar_sync table
        op.drop_table('task_calendar_sync')
        
        # Drop indexes from calendar_integrations
        op.drop_index('ix_calendar_integrations_provider', table_name='calendar_integrations')
        op.drop_index('ix_calendar_integrations_user_id', table_name='calendar_integrations')
        
        # Drop calendar_integrations table
        op.drop_table('calendar_integrations')
        
        # Drop indexes from webhook_deliveries
        op.drop_index('ix_webhook_deliveries_delivered_at', table_name='webhook_deliveries')
        op.drop_index('ix_webhook_deliveries_subscription_id', table_name='webhook_deliveries')
        
        # Drop webhook_deliveries table
        op.drop_table('webhook_deliveries')
        
        # Drop indexes from webhook_subscriptions
        op.drop_index('ix_webhook_subscriptions_project_id', table_name='webhook_subscriptions')
        op.drop_index('ix_webhook_subscriptions_user_id', table_name='webhook_subscriptions')
        
        # Drop webhook_subscriptions table
        op.drop_table('webhook_subscriptions')
        
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