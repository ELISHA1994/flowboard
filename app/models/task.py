from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.db.models import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    """Base task model with common attributes"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)

class TaskCreate(TaskBase):
    """Model for task creation"""
    status: TaskStatus = TaskStatus.TODO
    position: Optional[int] = Field(default=0, ge=0)
    category_ids: Optional[List[str]] = Field(default=[], description="List of category IDs")
    tag_names: Optional[List[str]] = Field(default=[], description="List of tag names")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for subtasks")
    depends_on_ids: Optional[List[str]] = Field(default=[], description="List of task IDs this task depends on")
    
    @field_validator('title')
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty or just whitespace')
        return v.strip()
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date and self.start_date:
            if self.due_date < self.start_date:
                raise ValueError('Due date must be after start date')
        return self

class TaskUpdate(BaseModel):
    """Model for task update (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)
    position: Optional[int] = Field(None, ge=0)
    category_ids: Optional[List[str]] = None
    tag_names: Optional[List[str]] = None
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for subtasks")
    depends_on_ids: Optional[List[str]] = Field(None, description="List of task IDs this task depends on")
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date and self.start_date:
            if self.due_date < self.start_date:
                raise ValueError('Due date must be after start date')
        return self

class TaskResponse(TaskBase):
    """Model for task response"""
    id: str
    status: TaskStatus
    user_id: str
    completed_at: Optional[datetime] = None
    actual_hours: float = 0.0
    position: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[dict] = []
    tags: List[dict] = []
    parent_task_id: Optional[str] = None
    subtasks: List['TaskResponse'] = []
    dependencies: List['TaskDependencyResponse'] = []
    dependents: List['TaskDependencyResponse'] = []

    model_config = ConfigDict(from_attributes=True)

class TaskTimeUpdate(BaseModel):
    """Model for updating task time tracking"""
    hours_to_add: float = Field(..., gt=0, le=24, description="Hours to add to actual_hours")


class TaskCategoryUpdate(BaseModel):
    """Model for updating task categories"""
    category_ids: List[str] = Field(..., description="List of category IDs to set")


class TaskTagUpdate(BaseModel):
    """Model for updating task tags"""
    tag_names: List[str] = Field(..., description="List of tag names to set")


class TaskDependencyBase(BaseModel):
    """Base model for task dependencies"""
    task_id: str = Field(..., description="ID of the task that has dependencies")
    depends_on_id: str = Field(..., description="ID of the task being depended on")


class TaskDependencyCreate(TaskDependencyBase):
    """Model for creating task dependencies"""
    pass


class TaskDependencyResponse(TaskDependencyBase):
    """Model for task dependency response"""
    id: str
    created_at: datetime
    depends_on: Optional[dict] = None  # Basic task info
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references for recursive models
TaskResponse.model_rebuild()