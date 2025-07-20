"""Add task assignment and sharing

Revision ID: add_task_assignment
Revises: 4d7525eb6be4
Create Date: 2025-07-19 17:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'add_task_assignment'
down_revision: Union[str, None] = '4d7525eb6be4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if assigned_to_id already exists before adding
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    columns = [col['name'] for col in inspector.get_columns('tasks')]
    if 'assigned_to_id' not in columns:
        op.add_column('tasks', sa.Column('assigned_to_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_tasks_assigned_to_id'), 'tasks', ['assigned_to_id'], unique=False)
    
    # Create task_shares table
    op.create_table('task_shares',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('shared_by_id', sa.String(), nullable=False),
        sa.Column('shared_with_id', sa.String(), nullable=False),
        sa.Column('permission', sa.Enum('VIEW', 'EDIT', 'COMMENT', name='tasksharepermission'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shared_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', 'shared_with_id', name='_task_share_uc')
    )


def downgrade() -> None:
    # Drop task_shares table
    op.drop_table('task_shares')
    
    # Remove assigned_to_id from tasks
    op.drop_index(op.f('ix_tasks_assigned_to_id'), table_name='tasks')
    op.drop_column('tasks', 'assigned_to_id')