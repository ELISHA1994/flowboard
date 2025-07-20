"""
Pydantic models for analytics and reporting functionality.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TimeLogCreate(BaseModel):
    """Model for creating a time log entry."""
    hours: float = Field(..., gt=0, description="Number of hours to log")
    description: Optional[str] = Field(None, max_length=500, description="Description of work done")
    logged_at: Optional[datetime] = Field(None, description="When the work was done (defaults to now)")


class TimeLogResponse(BaseModel):
    """Model for time log response."""
    id: str
    task_id: str
    user_id: str
    hours: float
    description: Optional[str]
    logged_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskStatistics(BaseModel):
    """Model for task statistics response."""
    total_tasks: int
    status_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    completion_rate: float
    average_completion_days: float
    overdue_tasks: int
    date_range: Dict[str, str]


class ProductivityTrend(BaseModel):
    """Model for a single productivity trend period."""
    period_start: str
    period_end: str
    tasks_created: int
    tasks_completed: int
    hours_logged: float


class ProductivityTrendsResponse(BaseModel):
    """Model for productivity trends response."""
    period_type: str
    trends: List[ProductivityTrend]


class TimeTrackingEntry(BaseModel):
    """Model for time tracking report entry."""
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    date: Optional[str] = None
    total_hours: float
    log_count: int


class TimeTrackingReport(BaseModel):
    """Model for time tracking report response."""
    total_hours: float
    group_by: str
    entries: List[TimeTrackingEntry]
    date_range: Dict[str, str]


class CategoryDistribution(BaseModel):
    """Model for category distribution."""
    category_id: str
    category_name: str
    color: str
    task_count: int


class TagDistribution(BaseModel):
    """Model for tag distribution."""
    tag_id: str
    tag_name: str
    color: str
    task_count: int


class TeamMemberPerformance(BaseModel):
    """Model for team member performance."""
    user_id: str
    username: str
    role: str
    tasks_assigned: int
    tasks_completed: int
    hours_logged: float


class TeamPerformanceReport(BaseModel):
    """Model for team performance report."""
    project_id: str
    project_name: str
    team_members: List[TeamMemberPerformance]


class ExportRequest(BaseModel):
    """Model for export request."""
    format: str = Field(..., pattern="^(csv|excel)$", description="Export format")
    task_ids: Optional[List[str]] = Field(None, description="Specific task IDs to export (all if not specified)")


class AnalyticsDateRange(BaseModel):
    """Model for analytics date range request."""
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
    project_id: Optional[str] = Field(None, description="Filter by project ID")


class TimeTrackingReportRequest(BaseModel):
    """Model for time tracking report request."""
    start_date: Optional[datetime] = Field(None, description="Start date for report")
    end_date: Optional[datetime] = Field(None, description="End date for report")
    group_by: str = Field(default="task", pattern="^(task|project|category|day)$", description="Group results by")