"""
Pydantic models for file attachments.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class FileAttachmentResponse(BaseModel):
    """Response model for file attachment"""
    id: str
    task_id: str
    uploaded_by_id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: Optional[str]
    created_at: datetime
    uploaded_by: Optional[dict] = None  # User info
    
    model_config = ConfigDict(from_attributes=True)


class FileAttachmentList(BaseModel):
    """Response model for list of file attachments"""
    attachments: list[FileAttachmentResponse]
    total: int


class FileUploadLimits(BaseModel):
    """Response model for file upload limits"""
    max_file_size: int = Field(..., description="Maximum file size in bytes")
    allowed_file_types: list[str] = Field(..., description="List of allowed file extensions")