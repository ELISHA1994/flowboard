from datetime import datetime
from typing import List, Optional

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)

from app.db.models import RecurrencePattern, TaskPriority, TaskStatus


class RecurrenceConfig(BaseModel):
    """Model for task recurrence configuration"""

    pattern: RecurrencePattern = Field(..., description="Recurrence pattern")
    interval: int = Field(
        default=1,
        ge=1,
        le=365,
        description="Interval for the pattern (e.g., every 2 days)",
    )
    days_of_week: Optional[List[int]] = Field(
        None, description="Days of week for weekly pattern (0=Mon, 6=Sun)"
    )
    day_of_month: Optional[int] = Field(
        None, ge=1, le=31, description="Day of month for monthly pattern"
    )
    month_of_year: Optional[int] = Field(
        None, ge=1, le=12, description="Month for yearly pattern"
    )
    end_date: Optional[datetime] = Field(None, description="When recurrence should end")
    count: Optional[int] = Field(
        None, ge=1, le=1000, description="Number of occurrences"
    )

    @model_validator(mode="after")
    def validate_pattern_fields(self):
        """Validate that required fields are provided for each pattern"""
        if self.pattern == RecurrencePattern.WEEKLY and not self.days_of_week:
            raise ValueError("days_of_week must be provided for weekly pattern")
        if self.pattern == RecurrencePattern.MONTHLY and not self.day_of_month:
            raise ValueError("day_of_month must be provided for monthly pattern")
        if self.pattern == RecurrencePattern.YEARLY and (
            not self.day_of_month or not self.month_of_year
        ):
            raise ValueError(
                "day_of_month and month_of_year must be provided for yearly pattern"
            )
        if self.end_date and self.count:
            raise ValueError("Cannot specify both end_date and count")
        return self


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
    category_ids: Optional[List[str]] = Field(
        default=[], description="List of category IDs"
    )
    tag_names: Optional[List[str]] = Field(default=[], description="List of tag names")
    parent_task_id: Optional[str] = Field(
        None, description="Parent task ID for subtasks"
    )
    depends_on_ids: Optional[List[str]] = Field(
        default=[], description="List of task IDs this task depends on"
    )
    project_id: Optional[str] = Field(
        None, description="Project ID to associate the task with"
    )
    assigned_to_id: Optional[str] = Field(
        None, description="User ID to assign the task to"
    )
    recurrence: Optional[RecurrenceConfig] = Field(
        None, description="Recurrence configuration"
    )

    @field_validator("title")
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty or just whitespace")
        return v.strip()

    @model_validator(mode="after")
    def validate_dates(self):
        if self.due_date and self.start_date:
            if self.due_date < self.start_date:
                raise ValueError("Due date must be after start date")
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
    parent_task_id: Optional[str] = Field(
        None, description="Parent task ID for subtasks"
    )
    depends_on_ids: Optional[List[str]] = Field(
        None, description="List of task IDs this task depends on"
    )
    project_id: Optional[str] = Field(
        None, description="Project ID to associate the task with"
    )
    assigned_to_id: Optional[str] = Field(
        None, description="User ID to assign the task to"
    )
    recurrence: Optional[RecurrenceConfig] = Field(
        None, description="Recurrence configuration"
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.due_date and self.start_date:
            if self.due_date < self.start_date:
                raise ValueError("Due date must be after start date")
        return self


class TaskResponse(TaskBase):
    """Model for task response"""

    id: str
    status: TaskStatus
    user_id: str
    project_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    actual_hours: float = 0.0
    position: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[dict] = []
    tags: List[dict] = []
    parent_task_id: Optional[str] = None
    subtasks: List["TaskResponse"] = []
    dependencies: List["TaskDependencyResponse"] = []
    dependents: List["TaskDependencyResponse"] = []
    project: Optional[dict] = None
    assigned_to: Optional[dict] = None

    # Recurrence fields
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_interval: Optional[int] = None
    recurrence_days_of_week: Optional[str] = None
    recurrence_day_of_month: Optional[int] = None
    recurrence_month_of_year: Optional[int] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = None
    recurrence_parent_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskTimeUpdate(BaseModel):
    """Model for updating task time tracking"""

    hours_to_add: float = Field(
        ..., gt=0, le=24, description="Hours to add to actual_hours"
    )


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


class TaskDependencyResponse(TaskDependencyBase):
    """Model for task dependency response"""

    id: str
    created_at: datetime
    depends_on: Optional[dict] = None  # Basic task info

    model_config = ConfigDict(from_attributes=True)


class TaskSharePermission(BaseModel):
    """Model for task share permissions"""

    permission: str = Field(..., description="Permission level: view, edit, or comment")


class TaskShareCreate(BaseModel):
    """Model for creating a task share"""

    task_id: str = Field(..., description="ID of the task to share")
    shared_with_id: str = Field(..., description="ID of the user to share with")
    permission: str = Field(
        default="view", description="Permission level: view, edit, or comment"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Optional expiration date for the share"
    )


class TaskShareResponse(BaseModel):
    """Model for task share response"""

    id: str
    task_id: str
    shared_by_id: str
    shared_with_id: str
    permission: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    task: Optional[dict] = None
    shared_by: Optional[dict] = None
    shared_with: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# Update forward references for recursive models
TaskResponse.model_rebuild()
