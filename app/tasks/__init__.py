"""
Background task definitions for the task management application.
"""
from app.core.celery_app import celery_app

__all__ = ["celery_app"]