"""
Centralized configuration for the application.
Handles environment variables and provides settings for different environments.
"""

import os
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Task Management API"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database
    # Build PostgreSQL URL from individual components if available
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "taskmanager")
    DB_USER: str = os.getenv("DB_USER", "taskmanageruser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "taskmanagerpass")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )

    # Database pool settings (for production databases)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Testing
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"
    TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", "taskmanager_test")
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}",
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # CORS Settings
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(",")

    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    # File Upload Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(
        os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024))
    )  # 10MB default
    ALLOWED_FILE_TYPES: list = os.getenv(
        "ALLOWED_FILE_TYPES",
        ".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.csv,.xlsx,.xls,.zip",
    ).split(",")
    SECURE_FILENAME_PATTERN: str = r"^[\w\-. ]+$"

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    REDIS_DEFAULT_TTL: int = int(
        os.getenv("REDIS_DEFAULT_TTL", "300")
    )  # 5 minutes default

    # Cache prefixes for different data types
    CACHE_PREFIX_TASKS: str = "tasks:"
    CACHE_PREFIX_USERS: str = "users:"
    CACHE_PREFIX_SEARCH: str = "search:"
    CACHE_PREFIX_ANALYTICS: str = "analytics:"
    CACHE_PREFIX_SESSION: str = "session:"

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL", ""
    )  # Will use redis_url if not set
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", ""
    )  # Will use redis_url if not set
    CELERY_TASK_SERIALIZER: str = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER: str = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT: list = os.getenv("CELERY_ACCEPT_CONTENT", "json").split(",")
    CELERY_TIMEZONE: str = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC: bool = os.getenv("CELERY_ENABLE_UTC", "True").lower() == "true"
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = int(
        os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "4")
    )
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = int(
        os.getenv("CELERY_WORKER_MAX_TASKS_PER_CHILD", "1000")
    )
    CELERY_TASK_ALWAYS_EAGER: bool = (
        os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"
    )
    CELERY_RESULT_EXPIRES: int = int(
        os.getenv("CELERY_RESULT_EXPIRES", "3600")
    )  # 1 hour

    # Background Task Settings
    RECURRING_TASK_CHECK_INTERVAL: int = int(
        os.getenv("RECURRING_TASK_CHECK_INTERVAL", "300")
    )  # 5 minutes
    REMINDER_CHECK_INTERVAL: int = int(
        os.getenv("REMINDER_CHECK_INTERVAL", "900")
    )  # 15 minutes
    NOTIFICATION_CLEANUP_INTERVAL: int = int(
        os.getenv("NOTIFICATION_CLEANUP_INTERVAL", "3600")
    )  # 1 hour
    ANALYTICS_CACHE_INTERVAL: int = int(
        os.getenv("ANALYTICS_CACHE_INTERVAL", "1800")
    )  # 30 minutes

    @property
    def database_settings(self) -> Dict[str, Any]:
        """Get database connection settings based on DATABASE_URL"""
        if self.DATABASE_URL.startswith("sqlite"):
            return {
                "url": self.DATABASE_URL,
                "connect_args": {"check_same_thread": False},
            }
        elif self.DATABASE_URL.startswith("postgresql"):
            return {
                "url": self.DATABASE_URL,
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_recycle": self.DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            }
        elif self.DATABASE_URL.startswith("mysql"):
            return {
                "url": self.DATABASE_URL,
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_recycle": self.DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            }
        else:
            return {"url": self.DATABASE_URL}

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test environment"""
        return self.TESTING or self.ENVIRONMENT.lower() == "testing"

    @property
    def redis_url(self) -> str:
        """Build Redis URL from configuration."""
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.is_testing:
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    def get_redis_config(self) -> dict:
        """Get Redis connection configuration."""
        config = {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "decode_responses": True,  # Automatically decode responses to strings
            "retry_on_timeout": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }

        if self.REDIS_PASSWORD:
            config["password"] = self.REDIS_PASSWORD

        # Use different database for testing
        if self.is_testing:
            config["db"] = self.REDIS_DB + 1

        return config

    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL, defaulting to Redis URL."""
        return self.CELERY_BROKER_URL or self.redis_url

    def get_celery_result_backend(self) -> str:
        """Get Celery result backend URL, defaulting to Redis URL."""
        return self.CELERY_RESULT_BACKEND or self.redis_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create a global settings instance
settings = get_settings()
