"""
Redis caching service for the task management application.
Provides centralized caching functionality with automatic serialization.
"""

import hashlib
import json
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from app.core.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service with automatic serialization and error handling.
    """

    def __init__(self):
        """Initialize Redis connection."""
        self._redis_client = None
        self._connection_pool = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Redis connection with connection pooling."""
        try:
            redis_config = settings.get_redis_config()

            # Create connection pool for better performance
            self._connection_pool = redis.ConnectionPool(**redis_config)
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)

            # Test connection
            self._redis_client.ping()
            logger.info("Redis connection established successfully")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Continue without caching
            self._redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._redis_client = None

    def _is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._redis_client:
            return False

        try:
            self._redis_client.ping()
            return True
        except RedisError:
            logger.warning("Redis connection lost, attempting to reconnect...")
            self._initialize_connection()
            return self._redis_client is not None

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage in Redis."""
        try:
            # Try JSON first for simple types (faster and human-readable)
            json.dumps(value)
            return json.dumps(value)
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects, encode to base64 for string storage
            import base64

            pickled = pickle.dumps(value)
            return "PICKLE:" + base64.b64encode(pickled).decode("utf-8")

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis."""
        if value.startswith("PICKLE:"):
            # This is a pickled value
            import base64

            pickled_data = base64.b64decode(value[7:])  # Remove "PICKLE:" prefix
            return pickle.loads(pickled_data)
        else:
            # Try JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return value

    def _build_key(self, prefix: str, identifier: str) -> str:
        """Build a standardized cache key."""
        # Include environment prefix to avoid conflicts
        env_prefix = f"{settings.ENVIRONMENT}:" if settings.ENVIRONMENT else ""
        return f"{env_prefix}{prefix}{identifier}"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not self._is_available():
            return default

        try:
            value = self._redis_client.get(key)
            if value is None:
                return default
            return self._deserialize_value(value)
        except RedisError as e:
            logger.warning(f"Failed to get cache key {key}: {e}")
            return default

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            nx: Only set if key doesn't exist

        Returns:
            True if value was set, False otherwise
        """
        if not self._is_available():
            return False

        try:
            serialized_value = self._serialize_value(value)
            ttl = ttl or settings.REDIS_DEFAULT_TTL

            result = self._redis_client.set(key, serialized_value, ex=ttl, nx=nx)
            return bool(result)
        except RedisError as e:
            logger.warning(f"Failed to set cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._is_available():
            return False

        try:
            result = self._redis_client.delete(key)
            return bool(result)
        except RedisError as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (Redis glob pattern)

        Returns:
            Number of keys deleted
        """
        if not self._is_available():
            return 0

        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                return self._redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Failed to delete pattern {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._is_available():
            return False

        try:
            return bool(self._redis_client.exists(key))
        except RedisError as e:
            logger.warning(f"Failed to check if key {key} exists: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if expiration was set, False otherwise
        """
        if not self._is_available():
            return False

        try:
            return bool(self._redis_client.expire(key, ttl))
        except RedisError as e:
            logger.warning(f"Failed to set expiration for key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None if operation failed
        """
        if not self._is_available():
            return None

        try:
            return self._redis_client.incrby(key, amount)
        except RedisError as e:
            logger.warning(f"Failed to increment key {key}: {e}")
            return None

    def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs
        """
        if not self._is_available() or not keys:
            return {}

        try:
            values = self._redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize_value(value)
            return result
        except RedisError as e:
            logger.warning(f"Failed to get multiple keys: {e}")
            return {}

    def set_multi(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs to set
            ttl: Time to live in seconds

        Returns:
            True if all values were set, False otherwise
        """
        if not self._is_available() or not mapping:
            return False

        try:
            # Serialize all values
            serialized_mapping = {
                key: self._serialize_value(value) for key, value in mapping.items()
            }

            # Use pipeline for better performance
            pipeline = self._redis_client.pipeline()
            pipeline.mset(serialized_mapping)

            # Set expiration for all keys if TTL is specified
            if ttl:
                for key in mapping.keys():
                    pipeline.expire(key, ttl)

            results = pipeline.execute()
            return all(results)
        except RedisError as e:
            logger.warning(f"Failed to set multiple keys: {e}")
            return False

    def flush_all(self) -> bool:
        """
        Clear all cache data (use with caution).

        Returns:
            True if cache was flushed, False otherwise
        """
        if not self._is_available():
            return False

        try:
            self._redis_client.flushdb()
            logger.info("Cache flushed successfully")
            return True
        except RedisError as e:
            logger.error(f"Failed to flush cache: {e}")
            return False


# Global cache service instance
cache_service = CacheService()


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Generated cache key
    """
    # Create a string representation of all arguments
    key_parts = []
    for arg in args:
        if hasattr(arg, "id"):
            key_parts.append(str(arg.id))
        else:
            key_parts.append(str(arg))

    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")

    # Create hash of the key parts to ensure consistent length
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(prefix: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching in testing unless explicitly enabled
            if settings.is_testing and not kwargs.pop("_use_cache", False):
                return func(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(*args, **kwargs)

            full_key = cache_service._build_key(prefix, cache_key_str)

            # Try to get from cache
            cached_result = cache_service.get(full_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {full_key}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(full_key, result, ttl)
            logger.debug(f"Cache miss, stored result for key: {full_key}")
            return result

        # Add cache invalidation method to the function
        def invalidate(*args, **kwargs):
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(*args, **kwargs)

            full_key = cache_service._build_key(prefix, cache_key_str)
            cache_service.delete(full_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user."""
    patterns = [
        f"*{settings.CACHE_PREFIX_USERS}{user_id}*",
        f"*{settings.CACHE_PREFIX_TASKS}*user:{user_id}*",
        f"*{settings.CACHE_PREFIX_SEARCH}*user:{user_id}*",
    ]

    for pattern in patterns:
        cache_service.delete_pattern(pattern)


def invalidate_task_cache(task_id: str, user_id: str = None):
    """Invalidate cache entries for a specific task."""
    patterns = [
        f"*{settings.CACHE_PREFIX_TASKS}{task_id}*",
        f"*{settings.CACHE_PREFIX_SEARCH}*",  # Search results might include this task
    ]

    if user_id:
        patterns.append(f"*{settings.CACHE_PREFIX_TASKS}*user:{user_id}*")

    for pattern in patterns:
        cache_service.delete_pattern(pattern)


def invalidate_project_cache(project_id: str):
    """Invalidate cache entries for a specific project."""
    patterns = [
        f"*project:{project_id}*",
        f"*{settings.CACHE_PREFIX_SEARCH}*",  # Search results might include project tasks
    ]

    for pattern in patterns:
        cache_service.delete_pattern(pattern)
