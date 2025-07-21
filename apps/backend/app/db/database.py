from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Get database settings
db_settings = settings.database_settings

# Create the SQLAlchemy engine with environment-specific settings
if settings.is_testing and settings.DATABASE_URL.startswith("sqlite"):
    # Use StaticPool for SQLite in testing to avoid connection issues
    engine = create_engine(
        settings.get_database_url(),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Remove 'url' from db_settings since we're passing it separately
    db_settings_without_url = {k: v for k, v in db_settings.items() if k != "url"}
    engine = create_engine(settings.get_database_url(), **db_settings_without_url)

# Enable foreign key constraints for SQLite
if settings.DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Creates a new database session for each request and closes it when done.
    This is used as a dependency in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context manager for Celery tasks
from contextlib import contextmanager


@contextmanager
def get_celery_db():
    """
    Context manager for database sessions in Celery tasks.
    Ensures proper commit/rollback handling.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
