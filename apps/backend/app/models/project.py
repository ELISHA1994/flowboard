"""
Pydantic models for Project API
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import ProjectRole


class ProjectBase(BaseModel):
    """Base model for project data"""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Project description"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name"""
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")
        return v


class ProjectCreate(ProjectBase):
    """Model for creating a new project"""


class ProjectUpdate(BaseModel):
    """Model for updating a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Project name cannot be empty")
        return v


class ProjectMemberResponse(BaseModel):
    """Model for project member response"""

    id: str
    user_id: str
    username: str
    email: str
    role: ProjectRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """Model for project response"""

    id: str
    owner_id: str
    owner_username: str
    is_active: bool = True
    task_count: int = 0
    member_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_role: Optional[ProjectRole] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with members"""

    members: List[ProjectMemberResponse] = []


class ProjectInvitationCreate(BaseModel):
    """Model for creating project invitation"""

    invitee_email: str = Field(
        ..., max_length=320, description="Email of the user to invite"
    )
    role: ProjectRole = Field(
        ProjectRole.MEMBER, description="Role to assign to the invitee"
    )

    @field_validator("invitee_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Invalid email format")
        return v


class ProjectInvitationResponse(BaseModel):
    """Model for project invitation response"""

    id: str
    project_id: str
    project_name: str
    inviter_name: str
    invitee_email: str
    role: ProjectRole
    token: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberUpdate(BaseModel):
    """Model for updating project member role"""

    role: ProjectRole = Field(..., description="New role for the member")


class ProjectTasksFilter(BaseModel):
    """Filter options for project tasks"""

    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    tag_name: Optional[str] = None
    category_id: Optional[str] = None
