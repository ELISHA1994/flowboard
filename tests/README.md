# FastAPI Testing Suite

This directory contains the comprehensive testing suite for the FastAPI Task Management application.

## Test Structure

```
tests/
├── unit/               # Isolated unit tests with mocked dependencies
│   ├── models/        # Pydantic model validation tests
│   ├── services/      # Business logic tests
│   └── utils/         # Utility function tests
├── integration/       # Integration tests with real database
│   ├── test_auth_endpoints.py
│   └── test_task_endpoints.py
├── e2e/              # End-to-end workflow tests
│   └── test_user_workflows.py
├── factories/        # Test data factories
└── conftest.py       # Shared pytest fixtures
```

## Running Tests

### Using pytest directly:
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m e2e           # End-to-end tests only

# Run with verbose output
pytest -v

# Run specific file
pytest tests/unit/services/test_task_service.py

# Run specific test
pytest tests/unit/models/test_task_models.py::TestTaskCreate::test_valid_task_create
```

### Using the test runner script:
```bash
# Run all tests
python run_tests.py all

# Run by category
python run_tests.py unit
python run_tests.py integration
python run_tests.py e2e

# Generate coverage report
python run_tests.py coverage

# Run specific file
python run_tests.py file tests/unit/services/test_task_service.py
```

### Using Make:
```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-e2e         # End-to-end tests only
make coverage         # Generate HTML coverage report
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Database**: Mocked, no real database connections
- **Dependencies**: All external dependencies mocked
- **Examples**: Model validation, service logic, utility functions

### Integration Tests
- **Purpose**: Test API endpoints with real database
- **Database**: SQLite in-memory database
- **Dependencies**: Real implementations
- **Examples**: Authentication flow, CRUD operations

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Database**: SQLite in-memory database
- **Dependencies**: Full application stack
- **Examples**: User registration → login → task management

## Key Testing Features

### Test Fixtures (conftest.py)
- `test_db`: In-memory SQLite database session
- `test_client`: FastAPI TestClient
- `test_user`: Pre-created test user
- `test_user_token`: JWT token for authenticated requests
- `authenticated_client`: TestClient with auth headers

### Test Factories
- `UserFactory`: Generate test users
- `TaskFactory`: Generate test tasks
- Uses `factory-boy` and `faker` for realistic test data

### Coverage Reporting
- Minimum coverage threshold: 80%
- HTML reports: `htmlcov/index.html`
- Terminal reports: Shows uncovered lines
- XML reports: For CI/CD integration

## Writing New Tests

### Unit Test Example:
```python
@pytest.mark.unit
class TestMyFeature:
    def test_feature_behavior(self):
        # Arrange
        mock_dependency = Mock()
        
        # Act
        result = my_function(mock_dependency)
        
        # Assert
        assert result == expected_value
```

### Integration Test Example:
```python
@pytest.mark.integration
class TestMyEndpoint:
    def test_endpoint_success(self, authenticated_client: TestClient):
        response = authenticated_client.post("/my-endpoint", json={"data": "value"})
        assert response.status_code == 200
```

### E2E Test Example:
```python
@pytest.mark.e2e
class TestUserJourney:
    def test_complete_workflow(self, test_client: TestClient):
        # Register user
        # Login
        # Perform actions
        # Verify final state
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names that explain what's being tested
3. **AAA Pattern**: Arrange, Act, Assert
4. **Fixtures**: Use fixtures for common setup
5. **Marks**: Always mark tests with appropriate category
6. **Coverage**: Aim for high coverage but focus on meaningful tests

## Continuous Integration

The project includes GitHub Actions workflow (`.github/workflows/tests.yml`) that:
- Runs all test categories
- Generates coverage reports
- Uploads coverage to Codecov
- Fails if coverage drops below 80%

## Troubleshooting

### Common Issues:
1. **Import Errors**: Ensure you're running from project root
2. **Database Errors**: Check SQLite is available
3. **Async Warnings**: Use `pytest-asyncio` markers for async tests
4. **Coverage Missing**: Install `pytest-cov` package

### Debug Mode:
```bash
# Run with full output
pytest -vv -s

# Run with pdb on failure
pytest --pdb

# Show local variables on failure
pytest -l
```