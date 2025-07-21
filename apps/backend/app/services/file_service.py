"""
Service layer for file attachment operations.
"""

import mimetypes
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import FileAttachment


class FileService:
    """Service for handling file operations"""

    @staticmethod
    def _ensure_upload_dir_exists():
        """Ensure upload directory exists"""
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_safe_filename(original_filename: str) -> str:
        """Generate a safe filename while preserving extension"""
        # Get file extension
        name, ext = os.path.splitext(original_filename)

        # Generate unique filename
        unique_name = f"{uuid.uuid4()}{ext}"
        return unique_name

    @staticmethod
    def _validate_file(file: UploadFile, file_content: Optional[bytes] = None) -> None:
        """Validate file type and size"""
        # Check file extension
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '{ext}' not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}",
            )

        # Validate filename pattern
        if not re.match(settings.SECURE_FILENAME_PATTERN, file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Only alphanumeric characters, hyphens, underscores, spaces, and dots are allowed",
            )

        # Check file size if content is provided
        if file_content and len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes",
            )

    @staticmethod
    async def upload_file(
        db: Session, task_id: str, user_id: str, file: UploadFile
    ) -> FileAttachment:
        """
        Upload a file attachment for a task.
        """
        # Ensure upload directory exists
        FileService._ensure_upload_dir_exists()

        # Generate safe filename
        safe_filename = FileService._generate_safe_filename(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        try:
            # Read file content
            content = await file.read()

            # Validate file (including size check)
            FileService._validate_file(file, content)

            # Save file to disk
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Detect MIME type
            mime_type = mimetypes.guess_type(file.filename)[0]

            # Create database record
            attachment = FileAttachment(
                id=str(uuid.uuid4()),
                task_id=task_id,
                uploaded_by_id=user_id,
                filename=safe_filename,
                original_filename=file.filename,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=file_path,
            )

            db.add(attachment)
            db.flush()

            return attachment

        except HTTPException:
            # Clean up file if validation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
        except Exception as e:
            # Clean up file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    @staticmethod
    def get_file_path(
        db: Session, attachment_id: str, user_id: str
    ) -> tuple[str, str, str]:
        """
        Get file path for download.
        Returns (file_path, original_filename, mime_type)
        """
        attachment = (
            db.query(FileAttachment).filter(FileAttachment.id == attachment_id).first()
        )

        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File attachment not found",
            )

        # Check if file exists on disk
        if not os.path.exists(attachment.storage_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk"
            )

        return (
            attachment.storage_path,
            attachment.original_filename,
            attachment.mime_type,
        )

    @staticmethod
    def delete_attachment(db: Session, attachment_id: str, user_id: str) -> bool:
        """
        Delete a file attachment.
        """
        attachment = (
            db.query(FileAttachment).filter(FileAttachment.id == attachment_id).first()
        )

        if not attachment:
            return False

        # Check permission (only uploader or task owner can delete)
        task = attachment.task
        if attachment.uploaded_by_id != user_id and task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this attachment",
            )

        # Delete file from disk
        if os.path.exists(attachment.storage_path):
            os.remove(attachment.storage_path)

        # Delete database record
        db.delete(attachment)

        return True

    @staticmethod
    def get_task_attachments(db: Session, task_id: str) -> List[FileAttachment]:
        """
        Get all attachments for a task.
        """
        return (
            db.query(FileAttachment)
            .filter(FileAttachment.task_id == task_id)
            .order_by(FileAttachment.created_at.desc())
            .all()
        )

    @staticmethod
    def can_user_access_attachment(
        db: Session, attachment: FileAttachment, user_id: str
    ) -> bool:
        """
        Check if user can access an attachment.
        """
        task = attachment.task

        # Task owner can always access
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

    @staticmethod
    def cleanup_orphaned_files():
        """
        Clean up files that don't have corresponding database records.
        This should be run as a periodic task.
        """
        if not os.path.exists(settings.UPLOAD_DIR):
            return

        # Get all files in upload directory
        upload_files = set(os.listdir(settings.UPLOAD_DIR))

        # Get all filenames from database
        # This would need database access in real implementation
        # For now, this is a placeholder
