from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class CategoryBase(BaseModel):
    """Base model for category data"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name or emoji")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate category name"""
        v = v.strip()
        if not v:
            raise ValueError("Category name cannot be empty")
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


class CategoryCreate(CategoryBase):
    """Model for creating a new category"""
    pass


class CategoryUpdate(BaseModel):
    """Model for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    
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


class CategoryResponse(CategoryBase):
    """Model for category response"""
    id: str
    is_active: bool = True
    task_count: int = 0
    created_at: str
    updated_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithTasks(CategoryResponse):
    """Category response with associated tasks"""
    tasks: List[dict] = []