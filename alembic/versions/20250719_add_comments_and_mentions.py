"""Add comments and mentions

Revision ID: add_comments_mentions
Revises: add_task_assignment
Create Date: 2025-07-19 19:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'add_comments_mentions'
down_revision: Union[str, None] = 'add_task_assignment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create comments table
    op.create_table('comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_comment_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_edited', sa.Boolean(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_task_id'), 'comments', ['task_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_comment_id'), 'comments', ['parent_comment_id'], unique=False)
    
    # Create comment_mentions table
    op.create_table('comment_mentions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('comment_id', sa.String(), nullable=False),
        sa.Column('mentioned_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentioned_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'mentioned_user_id', name='_comment_mention_uc')
    )
    op.create_index(op.f('ix_comment_mentions_mentioned_user_id'), 'comment_mentions', ['mentioned_user_id'], unique=False)


def downgrade() -> None:
    # Drop comment_mentions table
    op.drop_index(op.f('ix_comment_mentions_mentioned_user_id'), table_name='comment_mentions')
    op.drop_table('comment_mentions')
    
    # Drop comments table
    op.drop_index(op.f('ix_comments_parent_comment_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_user_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_task_id'), table_name='comments')
    op.drop_table('comments')