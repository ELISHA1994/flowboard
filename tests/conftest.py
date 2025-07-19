"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.database import Base, get_db
from app.db.models import User, Task
from app.core.middleware.jwt_auth_backend import create_access_token, get_password_hash
from datetime import timedelta
import uuid


# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a test database session for each test.
    Uses SQLite in-memory database for speed.
    """
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db: Session) -> TestClient:
    """
    Create a test client with the test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clear dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session) -> User:
    """
    Create a test user in the database.
    """
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    # Store the id to avoid detached session issues
    user_id = user.id
    # Reattach the object to ensure it's accessible
    test_db.expire_on_commit = False
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """
    Create a valid JWT token for the test user.
    """
    access_token_expires = timedelta(minutes=30)
    return create_access_token(
        data={"sub": test_user.username}, 
        expires_delta=access_token_expires
    )


@pytest.fixture
def authenticated_client(test_client: TestClient, test_user_token: str) -> TestClient:
    """
    Create a test client with authentication headers.
    """
    test_client.headers["Authorization"] = f"Bearer {test_user_token}"
    return test_client


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """
    Create authorization headers with the test user token.
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_task(test_db: Session, test_user: User) -> Task:
    """
    Create a test task in the database.
    """
    from app.db.models import TaskStatus, TaskPriority
    task = Task(
        id=str(uuid.uuid4()),
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        user_id=test_user.id,
        actual_hours=0.0,
        position=0
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    # Prevent detached session issues
    test_db.expire_on_commit = False
    return task


@pytest.fixture
def multiple_test_users(test_db: Session) -> list[User]:
    """
    Create multiple test users for testing user isolation.
    """
    users = []
    for i in range(3):
        user = User(
            id=str(uuid.uuid4()),
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        test_db.add(user)
        users.append(user)
    
    test_db.commit()
    for user in users:
        test_db.refresh(user)
    
    return users


@pytest.fixture
def sample_task_data() -> dict:
    """
    Provide sample task data for testing.
    """
    return {
        "title": "Sample Task",
        "description": "This is a sample task for testing",
        "status": "todo"
    }


@pytest.fixture
def sample_user_data() -> dict:
    """
    Provide sample user registration data for testing.
    """
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpass123"
    }


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )