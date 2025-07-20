"""
Analytics and reporting API endpoints.
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.core.middleware.jwt_auth_backend import get_current_user
from app.models.analytics import (
    TimeLogCreate, TimeLogResponse, TaskStatistics, ProductivityTrendsResponse,
    TimeTrackingReport, TimeTrackingReportRequest, CategoryDistribution,
    TagDistribution, TeamPerformanceReport, ExportRequest
)
from app.services.analytics_service import AnalyticsService
from app.services.task_service import TaskService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/tasks/{task_id}/time-log", response_model=TimeLogResponse)
async def log_time_to_task(
    task_id: str,
    time_log: TimeLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log time to a specific task."""
    # Verify task exists and user has access
    task = TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Add time to task
    updated_task = TaskService.add_time_to_task(
        db,
        task_id,
        current_user.id,
        time_log.hours,
        time_log.description,
        time_log.logged_at
    )
    
    if not updated_task:
        raise HTTPException(status_code=400, detail="Failed to log time")
    
    # Get the created time log
    time_log_entry = updated_task.time_logs[-1]  # Most recent entry
    
    return time_log_entry


@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    start_date: datetime = None,
    end_date: datetime = None,
    project_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall task statistics for the current user."""
    stats = AnalyticsService.get_task_statistics(
        db,
        current_user.id,
        start_date,
        end_date,
        project_id
    )
    return stats


@router.get("/productivity-trends", response_model=ProductivityTrendsResponse)
async def get_productivity_trends(
    period: str = "week",
    lookback: int = 4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get productivity trends over time."""
    if period not in ["week", "month", "quarter"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use week, month, or quarter")
    
    if lookback < 1 or lookback > 12:
        raise HTTPException(status_code=400, detail="Lookback must be between 1 and 12")
    
    trends = AnalyticsService.get_productivity_trends(
        db,
        current_user.id,
        period,
        lookback
    )
    return trends


@router.post("/time-tracking/report", response_model=TimeTrackingReport)
async def get_time_tracking_report(
    request: TimeTrackingReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed time tracking report."""
    report = AnalyticsService.get_time_tracking_report(
        db,
        current_user.id,
        request.start_date,
        request.end_date,
        request.group_by
    )
    return report


@router.get("/category-distribution", response_model=List[CategoryDistribution])
async def get_category_distribution(
    project_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task distribution by categories."""
    distribution = AnalyticsService.get_category_distribution(
        db,
        current_user.id,
        project_id
    )
    return distribution


@router.get("/tag-distribution", response_model=List[TagDistribution])
async def get_tag_distribution(
    project_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task distribution by tags."""
    distribution = AnalyticsService.get_tag_distribution(
        db,
        current_user.id,
        project_id
    )
    return distribution


@router.get("/team-performance/{project_id}", response_model=TeamPerformanceReport)
async def get_team_performance(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team performance metrics for a project."""
    report = AnalyticsService.get_team_performance(
        db,
        project_id,
        current_user.id
    )
    
    if not report:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    return report


@router.post("/export")
async def export_tasks(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export tasks to CSV or Excel format."""
    if export_request.format == "csv":
        content = AnalyticsService.export_tasks_csv(
            db,
            current_user.id,
            export_request.task_ids
        )
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    
    elif export_request.format == "excel":
        content = AnalyticsService.export_tasks_excel(
            db,
            current_user.id,
            export_request.task_ids
        )
        
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")