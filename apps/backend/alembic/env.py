"""
Alembic Environment Configuration

This file configures Alembic to work with our application's models and database settings.
It supports multiple database backends and environment-specific configurations.
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to Python path
sys.path.append(str(Path(__file__).parents[1]))

from app.core.config import settings
from app.db.database import Base

# Import all models to ensure they're registered with Base.metadata
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

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the sqlalchemy.url from our settings
config.set_main_option("sqlalchemy.url", settings.get_database_url())

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Custom function to control what objects are included in migrations.
    This can be used to exclude certain tables or other database objects.
    """
    # Example: Exclude the alembic_version table
    if type_ == "table" and name == "alembic_version":
        return False

    # Include all other objects
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database configuration
    db_config = config.get_section(config.config_ini_section, {})
    db_config["sqlalchemy.url"] = settings.get_database_url()

    # Handle SQLite-specific settings
    if settings.DATABASE_URL.startswith("sqlite"):
        db_config["sqlalchemy.connect_args"] = {"check_same_thread": False}

    # Create engine with appropriate settings
    connectable = engine_from_config(
        db_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Configure with additional options for better migration detection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            # PostgreSQL-specific options
            include_schemas=(
                True if settings.DATABASE_URL.startswith("postgresql") else False
            ),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print("Running migrations in OFFLINE mode")
    run_migrations_offline()
else:
    print(
        f"Running migrations in ONLINE mode against: {settings.ENVIRONMENT} environment"
    )
    run_migrations_online()
