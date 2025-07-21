from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.db.database import get_db
from app.db.models import Comment as CommentModel
from app.db.models import Task as TaskModel
from app.db.models import User as UserModel
from app.models.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.comment_service import CommentService
from app.services.notification_service import NotificationService
from app.tasks.activities import log_comment_added_async

router = APIRouter()


def format_comment_response(
    comment: CommentModel, include_replies: bool = True
) -> dict:
    """Format comment model for API response"""
    response = {
        "id": comment.id,
        "task_id": comment.task_id,
        "user_id": comment.user_id,
        "parent_comment_id": comment.parent_comment_id,
        "content": comment.content,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "is_edited": comment.is_edited,
        "user": {
            "id": comment.user.id,
            "username": comment.user.username,
            "email": comment.user.email,
        },
        "mentions": [
            {
                "id": mention.mentioned_user.id,
                "username": mention.mentioned_user.username,
                "email": mention.mentioned_user.email,
            }
            for mention in comment.mentions
        ],
        "replies": [],
    }

    # Include replies if requested
    if include_replies and hasattr(comment, "replies"):
        response["replies"] = [
            format_comment_response(reply, include_replies=False)
            for reply in comment.replies
        ]

    return response


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    task_id: str = Path(..., description="Task ID"),
    comment_data: CommentCreate = ...,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new comment on a task"""
    # Verify task exists
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found",
        )

    # Check if user can comment on this task
    if not CommentService.can_user_comment_on_task(db, task, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to comment on this task",
        )

    # If this is a reply, verify parent comment exists
    if comment_data.parent_comment_id:
        parent_comment = (
            db.query(CommentModel)
            .filter(
                CommentModel.id == comment_data.parent_comment_id,
                CommentModel.task_id == task_id,
            )
            .first()
        )
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent comment with id '{comment_data.parent_comment_id}' not found",
            )

    # Create comment with mentions
    comment = CommentService.create_comment_with_mentions(
        db,
        task_id=task_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
    )

    db.commit()
    db.refresh(comment)

    # Log comment creation activity
    log_comment_added_async.delay(
        task_id=task_id,
        user_id=current_user.id,
        comment_id=comment.id,
        comment_content=comment_data.content,
    )

    # Send notifications to mentioned users
    for mention in comment.mentions:
        NotificationService.notify_comment_mention(
            db, comment, mention.mentioned_user_id
        )

    return format_comment_response(comment)


@router.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
async def get_task_comments(
    task_id: str = Path(..., description="Task ID"),
    include_replies: bool = Query(True, description="Include nested replies"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all comments for a task"""
    # Verify task exists
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found",
        )

    # Check if user can view this task
    if not CommentService.can_user_comment_on_task(db, task, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view comments on this task",
        )

    # Get top-level comments
    comments = CommentService.get_task_comments(db, task_id)

    return [format_comment_response(comment, include_replies) for comment in comments]


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str = Path(..., description="Comment ID"),
    comment_update: CommentUpdate = ...,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a comment (only by the comment author)"""
    # Verify comment exists
    comment = db.query(CommentModel).filter(CommentModel.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id '{comment_id}' not found",
        )

    # Check if user owns the comment
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    # Update comment
    try:
        updated_comment = CommentService.update_comment(
            db,
            comment_id=comment_id,
            content=comment_update.content,
            user_id=current_user.id,
        )
        db.commit()
        db.refresh(updated_comment)

        return format_comment_response(updated_comment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str = Path(..., description="Comment ID"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a comment (only by the comment author)"""
    # Verify comment exists
    comment = db.query(CommentModel).filter(CommentModel.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id '{comment_id}' not found",
        )

    # Check if user owns the comment
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    # Delete comment
    if not CommentService.delete_comment(db, comment_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment",
        )

    db.commit()


@router.get("/users/me/mentions", response_model=List[dict])
async def get_my_mentions(
    limit: int = Query(50, ge=1, le=100, description="Number of mentions to return"),
    offset: int = Query(0, ge=0, description="Number of mentions to skip"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all mentions of the current user"""
    mentions = CommentService.get_user_mentions(
        db, user_id=current_user.id, limit=limit, offset=offset
    )

    result = []
    for mention in mentions:
        comment = mention.comment
        task = comment.task

        # Check if user can still view this task
        if CommentService.can_user_comment_on_task(db, task, current_user.id):
            result.append(
                {
                    "id": mention.id,
                    "comment_id": comment.id,
                    "task_id": task.id,
                    "task_title": task.title,
                    "comment_content": comment.content,
                    "mentioned_at": mention.created_at,
                    "mentioned_by": {
                        "id": comment.user.id,
                        "username": comment.user.username,
                        "email": comment.user.email,
                    },
                }
            )

    return result
