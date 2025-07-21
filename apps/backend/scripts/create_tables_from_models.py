#!/usr/bin/env python3
"""
Script to create all tables from SQLAlchemy models.
This is used when migrating to a fresh database.
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parents[1]))

from app.core.config import settings
from app.db.database import engine, Base
from app.db.models import (
    User,
    Task,
    TaskStatus,
    TaskPriority,
    Category,
    Tag,
    TaskDependency,
    Project,
    ProjectRole,
    ProjectMember,
    ProjectInvitation,
    TaskSharePermission,
    TaskShare,
    Comment,
    CommentMention,
    FileAttachment,
    RecurrencePattern,
    SavedSearch,
    TimeLog,
    WebhookSubscription,
    WebhookDelivery,
    CalendarIntegration,
    TaskCalendarSync,
    NotificationPreference,
    Notification,
    TaskReminder,
)


def create_all_tables():
    """Create all tables from the models."""
    print(f"Creating tables in database: {settings.get_database_url()}")
    print("This will create all tables defined in the models...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ All tables created successfully!")


if __name__ == "__main__":
    create_all_tables()
