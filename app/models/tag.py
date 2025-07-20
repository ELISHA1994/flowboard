from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class TagBase(BaseModel):
    """Base model for tag data"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field("#808080", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tag name"""
        v = v.strip().lower()  # Tags are lowercase by convention
        if not v:
            raise ValueError("Tag name cannot be empty")
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError("Tag name can only contain lowercase letters, numbers, hyphens, and underscores")
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color code"""
        v = v.upper()
        if not re.match(r'^#[0-9A-F]{6}$', v):
            raise ValueError("Color must be a valid hex code (e.g., #FF5733)")
        return v


class TagCreate(TagBase):
    """Model for creating a new tag"""


class TagUpdate(BaseModel):
    """Model for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate tag name"""
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            raise ValueError("Tag name cannot be empty")
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError("Tag name can only contain lowercase letters, numbers, hyphens, and underscores")
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate hex color code"""
        if v is None:
            return v
        v = v.upper()
        if not re.match(r'^#[0-9A-F]{6}$', v):
            raise ValueError("Color must be a valid hex code (e.g., #FF5733)")
        return v


class TagResponse(TagBase):
    """Model for tag response"""
    id: str
    task_count: int = 0
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)


class TagWithTasks(TagResponse):
    """Tag response with associated tasks"""
    tasks: List[dict] = []


class BulkTagOperation(BaseModel):
    """Model for bulk tag operations"""
    tag_names: List[str] = Field(..., min_length=1, max_length=20, description="List of tag names")
    
    @field_validator('tag_names')
    @classmethod
    def validate_tag_names(cls, v: List[str]) -> List[str]:
        """Validate and normalize tag names"""
        validated = []
        for name in v:
            name = name.strip().lower()
            if not name:
                continue
            if not re.match(r'^[a-z0-9_-]+$', name):
                raise ValueError(f"Invalid tag name: {name}")
            if name not in validated:  # Avoid duplicates
                validated.append(name)
        if not validated:
            raise ValueError("At least one valid tag name is required")
        return validated