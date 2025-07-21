"""
API endpoints for file attachments.
"""

from datetime import datetime

from fastapi import (APIRouter, Depends, File, HTTPException, Path, UploadFile,
                     status)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.db.database import get_db
from app.db.models import FileAttachment as FileAttachmentModel
from app.db.models import Task as TaskModel
from app.db.models import User as UserModel
from app.models.file_attachment import (FileAttachmentList,
                                        FileAttachmentResponse,
                                        FileUploadLimits)
from app.services.file_service import FileService
from app.tasks.activities import log_attachment_added_async

router = APIRouter()


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=FileAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file_attachment(
    task_id: str = Path(..., description="Task ID"),
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a file attachment to a task"""
    # Verify task exists
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found",
        )

    # Check if user can access this task
    # For uploading, we need to check task permissions directly
    can_access = False
    if task.user_id == current_user.id:
        can_access = True
    elif task.project_id and task.project:
        can_access = task.project.has_permission(current_user.id, "MEMBER")
    else:
        # Check if task is shared with the user with at least edit permission
        for share in task.shares:
            if share.shared_with_id == current_user.id and share.permission in [
                "edit",
                "comment",
            ]:
                if not share.expires_at or share.expires_at > datetime.utcnow():
                    can_access = True
                    break

    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add attachments to this task",
        )

    # Upload file
    try:
        attachment = await FileService.upload_file(
            db=db, task_id=task_id, user_id=current_user.id, file=file
        )
        db.commit()
        db.refresh(attachment)

        # Log file attachment activity
        log_attachment_added_async.delay(
            task_id=task_id,
            user_id=current_user.id,
            attachment_id=attachment.id,
            filename=attachment.original_filename,
            file_size=attachment.file_size,
        )

        # Format response
        response = FileAttachmentResponse(
            id=attachment.id,
            task_id=attachment.task_id,
            uploaded_by_id=attachment.uploaded_by_id,
            filename=attachment.filename,
            original_filename=attachment.original_filename,
            file_size=attachment.file_size,
            mime_type=attachment.mime_type,
            created_at=attachment.created_at,
            uploaded_by={
                "id": attachment.uploaded_by.id,
                "username": attachment.uploaded_by.username,
                "email": attachment.uploaded_by.email,
            },
        )

        return response
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/tasks/{task_id}/attachments", response_model=FileAttachmentList)
async def get_task_attachments(
    task_id: str = Path(..., description="Task ID"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all attachments for a task"""
    # Verify task exists
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found",
        )

    # Check if user can access this task
    # For viewing, we need to check task permissions directly
    can_access = False
    if task.user_id == current_user.id:
        can_access = True
    elif task.project_id and task.project:
        can_access = task.project.has_permission(current_user.id, "VIEWER")
    else:
        # Check if task is shared with the user
        for share in task.shares:
            if share.shared_with_id == current_user.id:
                if not share.expires_at or share.expires_at > datetime.utcnow():
                    can_access = True
                    break

    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view attachments for this task",
        )

    # Get attachments
    attachments = FileService.get_task_attachments(db, task_id)

    # Format response
    attachment_responses = []
    for attachment in attachments:
        attachment_responses.append(
            FileAttachmentResponse(
                id=attachment.id,
                task_id=attachment.task_id,
                uploaded_by_id=attachment.uploaded_by_id,
                filename=attachment.filename,
                original_filename=attachment.original_filename,
                file_size=attachment.file_size,
                mime_type=attachment.mime_type,
                created_at=attachment.created_at,
                uploaded_by={
                    "id": attachment.uploaded_by.id,
                    "username": attachment.uploaded_by.username,
                    "email": attachment.uploaded_by.email,
                },
            )
        )

    return FileAttachmentList(
        attachments=attachment_responses, total=len(attachment_responses)
    )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str = Path(..., description="Attachment ID"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Download a file attachment"""
    # Get attachment
    attachment = (
        db.query(FileAttachmentModel)
        .filter(FileAttachmentModel.id == attachment_id)
        .first()
    )

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        )

    # Check if user can access this attachment
    if not FileService.can_user_access_attachment(db, attachment, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this attachment",
        )

    # Get file path
    try:
        file_path, original_filename, mime_type = FileService.get_file_path(
            db, attachment_id, current_user.id
        )

        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type=mime_type or "application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}",
        )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str = Path(..., description="Attachment ID"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a file attachment"""
    try:
        success = FileService.delete_attachment(db, attachment_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
            )

        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attachment: {str(e)}",
        )


@router.get("/attachments/limits", response_model=FileUploadLimits)
async def get_upload_limits(current_user: UserModel = Depends(get_current_active_user)):
    """Get file upload limits"""
    return FileUploadLimits(
        max_file_size=settings.MAX_FILE_SIZE,
        allowed_file_types=settings.ALLOWED_FILE_TYPES,
    )
