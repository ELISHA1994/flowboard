"""
Background tasks for analytics computation and caching.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Project
from app.db.models import Task as TaskModel
from app.db.models import User
from app.services.analytics_service import AnalyticsService
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    def __call__(self, *args, **kwargs):
        with get_db() as db:
            return self.run_with_db(db, *args, **kwargs)

    def run_with_db(self, db: Session, *args, **kwargs):
        """Override this method instead of run()"""
        raise NotImplementedError


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def precompute_analytics(self, db: Session):
    """Precompute and cache analytics for all active users."""
    try:
        logger.info("Starting analytics precomputation")

        # Get all active users (users who have created tasks in the last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        active_users = (
            db.query(User)
            .join(TaskModel)
            .filter(TaskModel.created_at >= thirty_days_ago)
            .distinct()
            .all()
        )

        processed_count = 0
        cache_hits = 0

        for user in active_users:
            try:
                # Precompute user task statistics
                cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}task_stats:{user.id}"
                if not cache_service.exists(cache_key):
                    stats = AnalyticsService.get_task_statistics(db, user.id)
                    cache_service.set(cache_key, stats, ttl=1800)  # 30 minutes
                else:
                    cache_hits += 1

                # Precompute productivity trends
                cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}productivity:{user.id}"
                if not cache_service.exists(cache_key):
                    trends = AnalyticsService.get_productivity_trends(db, user.id)
                    cache_service.set(cache_key, trends, ttl=3600)  # 1 hour
                else:
                    cache_hits += 1

                # Precompute category and tag distributions
                cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}categories:{user.id}"
                if not cache_service.exists(cache_key):
                    categories = AnalyticsService.get_category_distribution(db, user.id)
                    cache_service.set(cache_key, categories, ttl=1800)  # 30 minutes
                else:
                    cache_hits += 1

                cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}tags:{user.id}"
                if not cache_service.exists(cache_key):
                    tags = AnalyticsService.get_tag_distribution(db, user.id)
                    cache_service.set(cache_key, tags, ttl=1800)  # 30 minutes
                else:
                    cache_hits += 1

                processed_count += 1

            except Exception as e:
                logger.error(
                    f"Error precomputing analytics for user {user.id}: {str(e)}"
                )
                continue

        logger.info(
            f"Analytics precomputation completed: {processed_count} users processed, {cache_hits} cache hits"
        )
        return {
            "success": True,
            "users_processed": processed_count,
            "cache_hits": cache_hits,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to precompute analytics: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def compute_user_analytics(
    self, db: Session, user_id: str, force_refresh: bool = False
):
    """Compute analytics for a specific user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found for analytics computation")
            return {"success": False, "reason": "User not found"}

        computed_metrics = []

        # Task statistics
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}task_stats:{user_id}"
        if force_refresh or not cache_service.exists(cache_key):
            stats = AnalyticsService.get_task_statistics(db, user_id)
            cache_service.set(cache_key, stats, ttl=1800)
            computed_metrics.append("task_statistics")

        # Productivity trends
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}productivity:{user_id}"
        if force_refresh or not cache_service.exists(cache_key):
            trends = AnalyticsService.get_productivity_trends(db, user_id)
            cache_service.set(cache_key, trends, ttl=3600)
            computed_metrics.append("productivity_trends")

        # Category distribution
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}categories:{user_id}"
        if force_refresh or not cache_service.exists(cache_key):
            categories = AnalyticsService.get_category_distribution(db, user_id)
            cache_service.set(cache_key, categories, ttl=1800)
            computed_metrics.append("category_distribution")

        # Tag distribution
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}tags:{user_id}"
        if force_refresh or not cache_service.exists(cache_key):
            tags = AnalyticsService.get_tag_distribution(db, user_id)
            cache_service.set(cache_key, tags, ttl=1800)
            computed_metrics.append("tag_distribution")

        logger.info(f"Computed analytics for user {user_id}: {computed_metrics}")
        return {
            "success": True,
            "user_id": user_id,
            "computed_metrics": computed_metrics,
            "force_refresh": force_refresh,
        }

    except Exception as e:
        logger.error(f"Failed to compute analytics for user {user_id}: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def compute_project_analytics(self, db: Session, project_id: str, user_id: str):
    """Compute analytics for a specific project."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project {project_id} not found for analytics computation")
            return {"success": False, "reason": "Project not found"}

        # Check user permission
        if not project.has_permission(user_id, "VIEWER"):
            logger.warning(
                f"User {user_id} does not have permission to view project {project_id} analytics"
            )
            return {"success": False, "reason": "Permission denied"}

        computed_metrics = []

        # Project task statistics
        cache_key = (
            f"{settings.CACHE_PREFIX_ANALYTICS}project_stats:{project_id}:{user_id}"
        )
        stats = AnalyticsService.get_task_statistics(db, user_id, project_id=project_id)
        cache_service.set(cache_key, stats, ttl=1800)
        computed_metrics.append("project_task_statistics")

        # Team performance
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}team_performance:{project_id}"
        performance = AnalyticsService.get_team_performance(db, project_id, user_id)
        cache_service.set(cache_key, performance, ttl=1800)
        computed_metrics.append("team_performance")

        # Project category distribution
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}project_categories:{project_id}:{user_id}"
        categories = AnalyticsService.get_category_distribution(
            db, user_id, project_id=project_id
        )
        cache_service.set(cache_key, categories, ttl=1800)
        computed_metrics.append("project_category_distribution")

        # Project tag distribution
        cache_key = (
            f"{settings.CACHE_PREFIX_ANALYTICS}project_tags:{project_id}:{user_id}"
        )
        tags = AnalyticsService.get_tag_distribution(db, user_id, project_id=project_id)
        cache_service.set(cache_key, tags, ttl=1800)
        computed_metrics.append("project_tag_distribution")

        logger.info(
            f"Computed project analytics for project {project_id}: {computed_metrics}"
        )
        return {
            "success": True,
            "project_id": project_id,
            "user_id": user_id,
            "computed_metrics": computed_metrics,
        }

    except Exception as e:
        logger.error(f"Failed to compute project analytics for {project_id}: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def generate_time_tracking_report(
    self,
    db: Session,
    user_id: str,
    start_date: str,
    end_date: str,
    group_by: str = "task",
):
    """Generate a time tracking report asynchronously."""
    try:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        report = AnalyticsService.get_time_tracking_report(
            db, user_id, start_dt, end_dt, group_by
        )

        # Cache the report for quick access
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}time_report:{user_id}:{start_date}:{end_date}:{group_by}"
        cache_service.set(cache_key, report, ttl=3600)  # 1 hour

        logger.info(f"Generated time tracking report for user {user_id}")
        return {
            "success": True,
            "user_id": user_id,
            "report_cache_key": cache_key,
            "total_hours": report["total_hours"],
            "entries_count": len(report["entries"]),
        }

    except Exception as e:
        logger.error(
            f"Failed to generate time tracking report for user {user_id}: {str(e)}"
        )
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def export_tasks_async(
    self, db: Session, user_id: str, task_ids: Optional[List[str]], format: str = "csv"
):
    """Export tasks asynchronously and cache the result."""
    try:
        if format.lower() == "csv":
            export_data = AnalyticsService.export_tasks_csv(db, user_id, task_ids)
            content_type = "text/csv"
        elif format.lower() == "excel":
            export_data = AnalyticsService.export_tasks_excel(db, user_id, task_ids)
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")

        # Cache the export data temporarily
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}export:{user_id}:{datetime.now(timezone.utc).timestamp()}"
        cache_service.set(
            cache_key,
            {
                "data": export_data,
                "content_type": content_type,
                "format": format,
                "task_count": len(task_ids) if task_ids else "all",
            },
            ttl=3600,
        )  # 1 hour

        logger.info(f"Generated {format} export for user {user_id}")
        return {
            "success": True,
            "user_id": user_id,
            "export_cache_key": cache_key,
            "format": format,
            "content_type": content_type,
        }

    except Exception as e:
        logger.error(f"Failed to export tasks for user {user_id}: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def cleanup_analytics_cache(self, db: Session):
    """Clean up expired analytics cache entries."""
    try:
        # Delete analytics cache entries that are older than 24 hours
        patterns_to_clean = [
            f"{settings.CACHE_PREFIX_ANALYTICS}export:*",
            f"{settings.CACHE_PREFIX_ANALYTICS}time_report:*",
        ]

        cleaned_count = 0
        for pattern in patterns_to_clean:
            count = cache_service.delete_pattern(pattern)
            cleaned_count += count

        logger.info(f"Cleaned up {cleaned_count} expired analytics cache entries")
        return {"success": True, "cleaned_count": cleaned_count}

    except Exception as e:
        logger.error(f"Failed to cleanup analytics cache: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def compute_system_wide_analytics(self, db: Session):
    """Compute system-wide analytics and metrics."""
    try:
        now = datetime.now(timezone.utc)

        # Count total users
        total_users = db.query(User).count()

        # Count active users (users with tasks in last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        active_users = (
            db.query(User)
            .join(TaskModel)
            .filter(TaskModel.created_at >= thirty_days_ago)
            .distinct()
            .count()
        )

        # Count total tasks
        total_tasks = db.query(TaskModel).count()

        # Count tasks created in last 30 days
        recent_tasks = (
            db.query(TaskModel).filter(TaskModel.created_at >= thirty_days_ago).count()
        )

        # Count total projects
        total_projects = db.query(Project).count()

        # Count active projects (projects with tasks in last 30 days)
        active_projects = (
            db.query(Project)
            .join(TaskModel)
            .filter(TaskModel.created_at >= thirty_days_ago)
            .distinct()
            .count()
        )

        system_metrics = {
            "timestamp": now.isoformat(),
            "users": {
                "total": total_users,
                "active_30_days": active_users,
                "activity_rate": (
                    (active_users / total_users * 100) if total_users > 0 else 0
                ),
            },
            "tasks": {
                "total": total_tasks,
                "created_30_days": recent_tasks,
                "average_per_user": (
                    (total_tasks / total_users) if total_users > 0 else 0
                ),
            },
            "projects": {
                "total": total_projects,
                "active_30_days": active_projects,
                "activity_rate": (
                    (active_projects / total_projects * 100)
                    if total_projects > 0
                    else 0
                ),
            },
        }

        # Cache system metrics
        cache_key = f"{settings.CACHE_PREFIX_ANALYTICS}system_metrics"
        cache_service.set(cache_key, system_metrics, ttl=3600)  # 1 hour

        logger.info("Computed system-wide analytics")
        return {"success": True, "metrics": system_metrics}

    except Exception as e:
        logger.error(f"Failed to compute system-wide analytics: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, base=DatabaseTask, queue="analytics")
def invalidate_user_analytics_cache(self, db: Session, user_id: str):
    """Invalidate analytics cache for a specific user."""
    try:
        patterns = [
            f"{settings.CACHE_PREFIX_ANALYTICS}task_stats:{user_id}*",
            f"{settings.CACHE_PREFIX_ANALYTICS}productivity:{user_id}*",
            f"{settings.CACHE_PREFIX_ANALYTICS}categories:{user_id}*",
            f"{settings.CACHE_PREFIX_ANALYTICS}tags:{user_id}*",
            f"{settings.CACHE_PREFIX_ANALYTICS}time_report:{user_id}*",
            f"{settings.CACHE_PREFIX_ANALYTICS}export:{user_id}*",
        ]

        invalidated_count = 0
        for pattern in patterns:
            count = cache_service.delete_pattern(pattern)
            invalidated_count += count

        logger.info(
            f"Invalidated {invalidated_count} analytics cache entries for user {user_id}"
        )
        return {"success": True, "invalidated_count": invalidated_count}

    except Exception as e:
        logger.error(
            f"Failed to invalidate analytics cache for user {user_id}: {str(e)}"
        )
        raise self.retry(countdown=60, max_retries=2)
