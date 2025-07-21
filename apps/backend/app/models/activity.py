"""
Pydantic models for task activity tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ActivityType


class ActivityResponse(BaseModel):
    """Response model for task activity"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    user_id: Optional[str] = None
    activity_type: ActivityType
    details: Optional[Dict[str, Any]] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    # User information (if available)
    user: Optional[dict] = None


class ActivityListResponse(BaseModel):
    """Response model for activity list with pagination"""

    activities: List[ActivityResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ActivityCreate(BaseModel):
    """Model for creating activities (mainly for system/admin use)"""

    task_id: str = Field(..., description="Task ID the activity belongs to")
    user_id: Optional[str] = Field(None, description="User ID who performed the action")
    activity_type: ActivityType = Field(..., description="Type of activity")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional activity details"
    )
    old_value: Optional[str] = Field(None, description="Previous value for changes")
    new_value: Optional[str] = Field(None, description="New value for changes")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ActivityFilter(BaseModel):
    """Model for filtering activities"""

    task_id: Optional[str] = Field(None, description="Filter by task ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    activity_types: Optional[List[ActivityType]] = Field(
        None, description="Filter by activity types"
    )
    start_date: Optional[datetime] = Field(
        None, description="Filter activities after this date"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter activities before this date"
    )
    limit: int = Field(
        default=50, ge=1, le=100, description="Number of activities to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of activities to skip")


class ActivityStats(BaseModel):
    """Response model for activity statistics"""

    total_activities: int
    activities_by_type: Dict[str, int]
    activities_by_user: Dict[str, int]
    most_active_day: Optional[str] = None
    most_active_hour: Optional[int] = None


class BulkActivityCreate(BaseModel):
    """Model for creating multiple activities in bulk"""

    activities: List[ActivityCreate] = Field(..., min_length=1, max_length=100)


class ActivitySummary(BaseModel):
    """Summary of activities for a task or user"""

    task_id: Optional[str] = None
    user_id: Optional[str] = None
    period_start: datetime
    period_end: datetime
    total_activities: int
    activity_breakdown: Dict[str, int]
    most_recent_activity: Optional[ActivityResponse] = None


class TaskActivityOverview(BaseModel):
    """Overview of all activities for a specific task"""

    task_id: str
    task_title: str
    total_activities: int
    latest_activity: Optional[ActivityResponse] = None
    activity_types: List[str]
    contributors: List[dict]  # Users who have performed activities on this task
    first_activity_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
