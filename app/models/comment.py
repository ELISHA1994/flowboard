from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class CommentBase(BaseModel):
    """Base comment model with common attributes"""
    content: str = Field(..., min_length=1, max_length=5000)
    
    @field_validator('content')
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Comment content cannot be empty or just whitespace')
        return v.strip()


class CommentCreate(CommentBase):
    """Model for creating a comment"""
    parent_comment_id: Optional[str] = Field(None, description="ID of parent comment for replies")


class CommentUpdate(BaseModel):
    """Model for updating a comment"""
    content: str = Field(..., min_length=1, max_length=5000)
    
    @field_validator('content')
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Comment content cannot be empty or just whitespace')
        return v.strip()


class MentionedUser(BaseModel):
    """Model for mentioned user info"""
    id: str
    username: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class CommentResponse(CommentBase):
    """Model for comment response"""
    id: str
    task_id: str
    user_id: str
    parent_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_edited: bool = False
    user: dict  # Basic user info
    mentions: List[MentionedUser] = []
    replies: List['CommentResponse'] = []
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references for recursive models
CommentResponse.model_rebuild()