"""
API endpoints for task activity tracking and audit logs.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.middleware.jwt_auth_backend import get_current_active_user
from app.db.database import get_db
from app.db.models import ActivityType
from app.db.models import Task as TaskModel
from app.db.models import TaskActivity
from app.db.models import User as UserModel
from app.models.activity import (ActivityCreate, ActivityFilter,
                                 ActivityListResponse, ActivityResponse,
                                 ActivityStats, ActivitySummary,
                                 BulkActivityCreate, TaskActivityOverview)
from app.services.activity_service import ActivityService
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)
router = APIRouter()


def format_activity_response(activity: TaskActivity) -> dict:
    """Format activity model for API response"""
    import json

    # Parse JSON details if it's a string
    details = None
    if activity.details:
        try:
            details = (
                json.loads(activity.details)
                if isinstance(activity.details, str)
                else activity.details
            )
        except json.JSONDecodeError:
            details = activity.details

    response = {
        "id": activity.id,
        "task_id": activity.task_id,
        "user_id": activity.user_id,
        "activity_type": activity.activity_type,
        "details": details,
        "old_value": activity.old_value,
        "new_value": activity.new_value,
        "ip_address": activity.ip_address,
        "user_agent": activity.user_agent,
        "created_at": activity.created_at,
        "user": None,
    }

    # Include user info if available
    if activity.user:
        response["user"] = {
            "id": activity.user.id,
            "username": activity.user.username,
            "email": activity.user.email,
        }

    return response


@router.get("/tasks/{task_id}/activities", response_model=ActivityListResponse)
def get_task_activities(
    task_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    activity_types: Optional[List[ActivityType]] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get activities for a specific task.
    """
    # Check if task exists and user has access
    task = TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )

    activities = ActivityService.get_task_activities(
        db=db,
        task_id=task_id,
        limit=limit,
        offset=offset,
        activity_types=activity_types,
    )

    # Count total activities for pagination
    total_query = db.query(TaskActivity).filter(TaskActivity.task_id == task_id)
    if activity_types:
        total_query = total_query.filter(TaskActivity.activity_type.in_(activity_types))
    total = total_query.count()

    formatted_activities = [
        format_activity_response(activity) for activity in activities
    ]

    return ActivityListResponse(
        activities=formatted_activities,
        total=total,
        page=(offset // limit) + 1,
        per_page=limit,
        has_next=offset + limit < total,
        has_prev=offset > 0,
    )


@router.get("/users/{user_id}/activities", response_model=ActivityListResponse)
def get_user_activities(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    activity_types: Optional[List[ActivityType]] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get activities performed by a specific user.
    Users can only view their own activities unless they're admin.
    """
    # Check access - users can only view their own activities
    if user_id != current_user.id:
        # TODO: Add admin role check here if needed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own activities",
        )

    activities = ActivityService.get_user_activities(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        activity_types=activity_types,
    )

    # Count total activities for pagination
    total_query = db.query(TaskActivity).filter(TaskActivity.user_id == user_id)
    if activity_types:
        total_query = total_query.filter(TaskActivity.activity_type.in_(activity_types))
    total = total_query.count()

    formatted_activities = [
        format_activity_response(activity) for activity in activities
    ]

    return ActivityListResponse(
        activities=formatted_activities,
        total=total,
        page=(offset // limit) + 1,
        per_page=limit,
        has_next=offset + limit < total,
        has_prev=offset > 0,
    )


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get a specific activity by ID.
    """
    activity = db.query(TaskActivity).filter(TaskActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )

    # Check if user has access to the task this activity belongs to
    task = TaskService.get_task_by_id(db, activity.task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )

    return format_activity_response(activity)


@router.post("/activities", response_model=ActivityResponse)
def create_activity(
    activity_data: ActivityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Create a new activity entry.
    This is mainly for admin/system use or manual activity logging.
    """
    # Check if task exists and user has access
    task = TaskService.get_task_by_id(db, activity_data.task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )

    # Extract IP address and user agent from request
    ip_address = activity_data.ip_address or request.client.host
    user_agent = activity_data.user_agent or request.headers.get("User-Agent")

    activity = ActivityService.log_activity(
        db=db,
        task_id=activity_data.task_id,
        user_id=activity_data.user_id or current_user.id,
        activity_type=activity_data.activity_type,
        details=activity_data.details,
        old_value=activity_data.old_value,
        new_value=activity_data.new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return format_activity_response(activity)


@router.post("/activities/bulk", response_model=List[ActivityResponse])
def create_bulk_activities(
    bulk_data: BulkActivityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Create multiple activities in bulk.
    This is mainly for system use or data migration.
    """
    results = []

    for activity_data in bulk_data.activities:
        try:
            # Check if task exists and user has access
            task = TaskService.get_task_by_id(
                db, activity_data.task_id, current_user.id
            )
            if not task:
                logger.warning(
                    f"Skipping activity for task {activity_data.task_id} - not found or access denied"
                )
                continue

            # Extract IP address and user agent from request
            ip_address = activity_data.ip_address or request.client.host
            user_agent = activity_data.user_agent or request.headers.get("User-Agent")

            activity = ActivityService.log_activity(
                db=db,
                task_id=activity_data.task_id,
                user_id=activity_data.user_id or current_user.id,
                activity_type=activity_data.activity_type,
                details=activity_data.details,
                old_value=activity_data.old_value,
                new_value=activity_data.new_value,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            results.append(format_activity_response(activity))

        except Exception as e:
            logger.error(
                f"Failed to create activity for task {activity_data.task_id}: {str(e)}"
            )
            continue

    return results


@router.get("/tasks/{task_id}/activities/overview", response_model=TaskActivityOverview)
def get_task_activity_overview(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get an overview of all activities for a specific task.
    """
    # Check if task exists and user has access
    task = TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )

    # Get all activities for the task
    activities = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).all()

    if not activities:
        return TaskActivityOverview(
            task_id=task_id,
            task_title=task.title,
            total_activities=0,
            latest_activity=None,
            activity_types=[],
            contributors=[],
            first_activity_date=None,
            last_activity_date=None,
        )

    # Get unique activity types
    activity_types = list(
        set([activity.activity_type.value for activity in activities])
    )

    # Get unique contributors
    user_ids = list(
        set([activity.user_id for activity in activities if activity.user_id])
    )
    contributors = []
    if user_ids:
        users = db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        contributors = [{"id": user.id, "username": user.username} for user in users]

    # Get latest activity
    latest_activity = max(activities, key=lambda a: a.created_at)

    # Get date range
    first_activity_date = min(activities, key=lambda a: a.created_at).created_at
    last_activity_date = max(activities, key=lambda a: a.created_at).created_at

    return TaskActivityOverview(
        task_id=task_id,
        task_title=task.title,
        total_activities=len(activities),
        latest_activity=format_activity_response(latest_activity),
        activity_types=activity_types,
        contributors=contributors,
        first_activity_date=first_activity_date,
        last_activity_date=last_activity_date,
    )


@router.get("/activities/stats", response_model=ActivityStats)
def get_activity_stats(
    task_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get activity statistics with optional filters.
    """
    query = db.query(TaskActivity)

    # Apply filters
    if task_id:
        # Check access to task
        task = TaskService.get_task_by_id(db, task_id, current_user.id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )
        query = query.filter(TaskActivity.task_id == task_id)

    if user_id:
        # Users can only view their own stats unless admin
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own activity stats",
            )
        query = query.filter(TaskActivity.user_id == user_id)

    if start_date:
        query = query.filter(TaskActivity.created_at >= start_date)

    if end_date:
        query = query.filter(TaskActivity.created_at <= end_date)

    activities = query.all()

    # Calculate statistics
    total_activities = len(activities)

    # Activities by type
    activities_by_type = {}
    for activity in activities:
        activity_type = activity.activity_type.value
        activities_by_type[activity_type] = activities_by_type.get(activity_type, 0) + 1

    # Activities by user
    activities_by_user = {}
    for activity in activities:
        if activity.user_id:
            activities_by_user[activity.user_id] = (
                activities_by_user.get(activity.user_id, 0) + 1
            )

    # Most active day and hour (simplified)
    most_active_day = None
    most_active_hour = None

    if activities:
        # Group by day of week
        day_counts = {}
        hour_counts = {}

        for activity in activities:
            day = activity.created_at.strftime("%A")
            hour = activity.created_at.hour

            day_counts[day] = day_counts.get(day, 0) + 1
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        most_active_day = max(day_counts, key=day_counts.get) if day_counts else None
        most_active_hour = (
            max(hour_counts, key=hour_counts.get) if hour_counts else None
        )

    return ActivityStats(
        total_activities=total_activities,
        activities_by_type=activities_by_type,
        activities_by_user=activities_by_user,
        most_active_day=most_active_day,
        most_active_hour=most_active_hour,
    )


@router.delete("/activities/cleanup")
def cleanup_old_activities(
    days: int = Query(default=365, ge=1, le=3650),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Clean up old activity records.
    This is an admin-only operation for database maintenance.
    """
    # TODO: Add admin role check here
    # For now, any authenticated user can trigger cleanup

    deleted_count = ActivityService.cleanup_old_activities(db, days)

    return {
        "success": True,
        "message": f"Cleaned up {deleted_count} activity records older than {days} days",
    }
