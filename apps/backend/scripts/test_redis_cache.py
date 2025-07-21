#!/usr/bin/env python3
"""
Script to test Redis caching functionality.
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parents[1]))

from app.services.cache_service import cache_service
from app.core.config import settings
import time
import json


def test_redis_connection():
    """Test basic Redis connection."""
    print("Testing Redis connection...")

    if not cache_service._is_available():
        print("❌ Redis is not available")
        return False

    print("✅ Redis connection successful")
    return True


def test_basic_cache_operations():
    """Test basic cache operations."""
    print("\nTesting basic cache operations...")

    # Test string value
    key = "test:string"
    value = "Hello, Redis!"

    # Set value
    result = cache_service.set(key, value, ttl=60)
    if not result:
        print("❌ Failed to set cache value")
        return False

    # Get value
    retrieved = cache_service.get(key)
    if retrieved != value:
        print(f"❌ Cache value mismatch. Expected: {value}, Got: {retrieved}")
        return False

    print("✅ String caching works")

    # Test complex object
    key = "test:object"
    value = {
        "user_id": "123",
        "tasks": [
            {"id": "1", "title": "Task 1", "completed": False},
            {"id": "2", "title": "Task 2", "completed": True},
        ],
        "metadata": {"created_at": "2025-01-01T00:00:00Z"},
    }

    cache_service.set(key, value, ttl=60)
    retrieved = cache_service.get(key)

    if retrieved != value:
        print("❌ Complex object caching failed")
        return False

    print("✅ Complex object caching works")

    # Test deletion
    cache_service.delete(key)
    retrieved = cache_service.get(key)

    if retrieved is not None:
        print("❌ Cache deletion failed")
        return False

    print("✅ Cache deletion works")
    return True


def test_cache_expiration():
    """Test cache expiration."""
    print("\nTesting cache expiration...")

    key = "test:expiration"
    value = "This should expire"

    # Set with 2 second TTL
    cache_service.set(key, value, ttl=2)

    # Should be available immediately
    retrieved = cache_service.get(key)
    if retrieved != value:
        print("❌ Value not available immediately after setting")
        return False

    print("✅ Value available immediately")

    # Wait for expiration
    print("Waiting 3 seconds for expiration...")
    time.sleep(3)

    # Should be expired now
    retrieved = cache_service.get(key)
    if retrieved is not None:
        print(f"❌ Value should have expired but got: {retrieved}")
        return False

    print("✅ Cache expiration works")
    return True


def test_cache_patterns():
    """Test pattern-based cache operations."""
    print("\nTesting pattern-based operations...")

    # Set multiple keys with same prefix
    prefix = "test:pattern:"
    keys = [f"{prefix}1", f"{prefix}2", f"{prefix}3"]

    for i, key in enumerate(keys):
        cache_service.set(key, f"value_{i}", ttl=60)

    # Delete by pattern
    deleted_count = cache_service.delete_pattern(f"{prefix}*")

    if deleted_count != 3:
        print(f"❌ Expected to delete 3 keys, deleted {deleted_count}")
        return False

    # Verify keys are deleted
    for key in keys:
        if cache_service.get(key) is not None:
            print(f"❌ Key {key} should have been deleted")
            return False

    print("✅ Pattern deletion works")
    return True


def test_cache_multi_operations():
    """Test multi-key operations."""
    print("\nTesting multi-key operations...")

    # Test multi-set
    mapping = {
        "multi:1": "value1",
        "multi:2": {"nested": "value2"},
        "multi:3": [1, 2, 3],
    }

    result = cache_service.set_multi(mapping, ttl=60)
    if not result:
        print("❌ Multi-set failed")
        return False

    # Test multi-get
    keys = list(mapping.keys())
    retrieved = cache_service.get_multi(keys)

    if len(retrieved) != len(mapping):
        print(f"❌ Multi-get returned {len(retrieved)} items, expected {len(mapping)}")
        return False

    for key, expected_value in mapping.items():
        if key not in retrieved or retrieved[key] != expected_value:
            print(f"❌ Multi-get value mismatch for key {key}")
            assert False, f"Multi-get value mismatch for key {key}"

    print("✅ Multi-key operations work")

    # Clean up
    for key in keys:
        cache_service.delete(key)

    assert True, "Multi-key operations work correctly"


def test_cache_configuration():
    """Test cache configuration."""
    print("\nTesting cache configuration...")

    print(f"Redis Host: {settings.REDIS_HOST}")
    print(f"Redis Port: {settings.REDIS_PORT}")
    print(f"Redis DB: {settings.REDIS_DB}")
    print(f"Default TTL: {settings.REDIS_DEFAULT_TTL}")
    print(f"Redis URL: {settings.redis_url}")

    config = settings.get_redis_config()
    print(f"Redis Config: {json.dumps(config, indent=2)}")

    return True


def main():
    """Run all cache tests."""
    print("🔧 Redis Cache Test Suite")
    print("=" * 40)

    tests = [
        test_redis_connection,
        test_cache_configuration,
        test_basic_cache_operations,
        test_cache_expiration,
        test_cache_patterns,
        test_cache_multi_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 40)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All cache tests passed!")
        return 0
    else:
        print("💥 Some cache tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
