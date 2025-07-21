"""
Service layer for comment operations and @mention handling.
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from app.db.models import Comment, CommentMention, Task, User


class CommentService:
    """Service for handling comment operations"""

    @staticmethod
    def parse_mentions(content: str) -> Set[str]:
        """
        Parse @mentions from comment content.
        Returns a set of mentioned usernames.
        """
        # Match @username pattern (alphanumeric and underscore)
        mention_pattern = r"@(\w+)"
        mentions = re.findall(mention_pattern, content)
        return set(mentions)

    @staticmethod
    def create_comment_with_mentions(
        db: Session,
        task_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ) -> Comment:
        """
        Create a comment and handle @mentions.
        """
        # Create the comment
        comment = Comment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_comment_id,
        )
        db.add(comment)
        db.flush()  # Flush to get the comment ID

        # Parse and create mentions
        mentioned_usernames = CommentService.parse_mentions(content)
        for username in mentioned_usernames:
            # Find the user by username
            mentioned_user = db.query(User).filter(User.username == username).first()

            if mentioned_user and mentioned_user.id != user_id:
                # Create mention record
                mention = CommentMention(
                    id=str(uuid.uuid4()),
                    comment_id=comment.id,
                    mentioned_user_id=mentioned_user.id,
                )
                db.add(mention)

        return comment

    @staticmethod
    def update_comment(
        db: Session, comment_id: str, content: str, user_id: str
    ) -> Comment:
        """
        Update a comment and handle updated mentions.
        """
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.user_id == user_id)
            .first()
        )

        if not comment:
            raise ValueError(
                "Comment not found or you don't have permission to edit it"
            )

        # Update content
        comment.content = content
        comment.is_edited = True

        # Clear existing mentions
        db.query(CommentMention).filter(
            CommentMention.comment_id == comment_id
        ).delete()

        # Parse and create new mentions
        mentioned_usernames = CommentService.parse_mentions(content)
        for username in mentioned_usernames:
            mentioned_user = db.query(User).filter(User.username == username).first()

            if mentioned_user and mentioned_user.id != user_id:
                mention = CommentMention(
                    id=str(uuid.uuid4()),
                    comment_id=comment.id,
                    mentioned_user_id=mentioned_user.id,
                )
                db.add(mention)

        return comment

    @staticmethod
    def get_task_comments(
        db: Session, task_id: str, parent_comment_id: Optional[str] = None
    ) -> List[Comment]:
        """
        Get comments for a task, optionally filtered by parent comment.
        """
        query = db.query(Comment).filter(Comment.task_id == task_id)

        if parent_comment_id is None:
            # Get top-level comments only
            query = query.filter(Comment.parent_comment_id.is_(None))
        else:
            # Get replies to a specific comment
            query = query.filter(Comment.parent_comment_id == parent_comment_id)

        return query.order_by(Comment.created_at.asc()).all()

    @staticmethod
    def get_user_mentions(
        db: Session, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[CommentMention]:
        """
        Get all mentions for a user across all tasks.
        """
        return (
            db.query(CommentMention)
            .filter(CommentMention.mentioned_user_id == user_id)
            .order_by(CommentMention.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def delete_comment(db: Session, comment_id: str, user_id: str) -> bool:
        """
        Delete a comment if the user owns it.
        """
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.user_id == user_id)
            .first()
        )

        if not comment:
            return False

        # Delete the comment (cascades to mentions and replies)
        db.delete(comment)
        return True

    @staticmethod
    def can_user_comment_on_task(db: Session, task: Task, user_id: str) -> bool:
        """
        Check if a user can comment on a task.
        """
        # Task owner can always comment
        if task.user_id == user_id:
            return True

        # If task belongs to a project, check project membership
        if task.project_id and task.project:
            return task.project.has_permission(user_id, "VIEWER")

        # Check if task is shared with the user
        for share in task.shares:
            if share.shared_with_id == user_id:
                # Check if share hasn't expired
                if not share.expires_at or share.expires_at > datetime.utcnow():
                    return True

        return False
