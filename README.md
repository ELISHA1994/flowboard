# Task Management API - Clean Architecture

A scalable FastAPI application following clean architecture principles with JWT authentication, SQLite database persistence, and comprehensive task management features.

## Project Structure

```
app/
├── api/                 # API endpoints and routing
│   ├── main.py         # Main API router aggregator
│   └── routers/        # Individual route modules
│       ├── auth.py     # Authentication endpoints
│       ├── tasks.py    # Task CRUD endpoints
│       └── users.py    # User profile endpoints
├── core/               # Core application components
│   ├── exception_handlers.py  # Global exception handling
│   ├── logging.py             # Logging configuration
│   ├── middleware/            # Middleware components
│   │   └── jwt_auth_backend.py  # JWT authentication
│   └── models.py              # Core response models
├── db/                 # Database layer
│   ├── database.py     # Database connection setup
│   ├── db_instance.py  # Database dependency injection
│   └── models.py       # SQLAlchemy ORM models
├── models/             # Pydantic models (DTOs)
│   ├── task.py        # Task request/response models
│   └── user.py        # User request/response models
├── services/           # Business logic layer
│   ├── task_service.py # Task-related business logic
│   └── user_service.py # User-related business logic
├── utils/              # Utilities and constants
│   └── constants.py    # Application constants
└── main.py            # FastAPI application entry point

tests/                  # Comprehensive test suite
├── unit/              # Unit tests (isolated, mocked)
├── integration/       # Integration tests (with database)
├── e2e/              # End-to-end workflow tests
├── factories/        # Test data factories
└── conftest.py       # Shared pytest fixtures
```

## Prerequisites

- Python 3.8+
- Virtual environment (venv)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd turing_interview
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Install application dependencies
   pip install -r requirements.txt
   
   # Install test dependencies
   pip install -r requirements-test.txt
   ```
   
   Or install manually:
   ```bash
   # Core dependencies
   pip install fastapi uvicorn sqlalchemy python-jose[cryptography] bcrypt python-multipart email-validator python-dotenv
   
   # Test dependencies
   pip install pytest pytest-asyncio pytest-cov httpx factory-boy faker
   ```

## Configuration

1. **Environment Variables:**
   Create a `.env` file in the project root:
   ```env
   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

   To generate a secure secret key:
   ```bash
   openssl rand -hex 32
   ```

## Running the Application

1. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

   Or specify a different port:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

2. **Access the API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Testing

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term
```

### Running Tests

The project includes a comprehensive test suite with unit, integration, and end-to-end tests.

1. **Run all tests with coverage:**
   ```bash
   pytest
   # or
   make test
   ```

2. **Run specific test categories:**
   ```bash
   # Unit tests only (mocked dependencies)
   pytest -m unit
   # or
   python run_tests.py unit
   # or
   make test-unit
   
   # Integration tests only (with database)
   pytest -m integration
   # or
   python run_tests.py integration
   # or
   make test-integration
   
   # End-to-end tests only (complete workflows)
   pytest -m e2e
   # or
   python run_tests.py e2e
   # or
   make test-e2e
   ```

3. **Run specific test files:**
   ```bash
   # Run a specific test file
   pytest tests/unit/services/test_task_service.py
   
   # Run a specific test class
   pytest tests/unit/models/test_task_models.py::TestTaskCreate
   
   # Run a specific test method
   pytest tests/unit/models/test_task_models.py::TestTaskCreate::test_valid_task_create
   ```

4. **Generate coverage reports:**
   ```bash
   # Generate HTML coverage report
   pytest --cov=app --cov-report=html
   # or
   python run_tests.py coverage
   # or
   make coverage
   
   # View the report
   open htmlcov/index.html  # On macOS
   # or
   xdg-open htmlcov/index.html  # On Linux
   # or
   start htmlcov/index.html  # On Windows
   ```

5. **Run tests with different options:**
   ```bash
   # Verbose output
   pytest -v
   
   # Show print statements
   pytest -s
   
   # Run failed tests first
   pytest --failed-first
   
   # Run only last failed tests
   pytest --last-failed
   
   # Run tests in parallel (requires pytest-xdist)
   pytest -n auto
   ```

### Test Categories

- **Unit Tests** (`tests/unit/`): Test individual components in isolation with mocked dependencies
  - Model validation tests
  - Service logic tests
  - Utility function tests
  
- **Integration Tests** (`tests/integration/`): Test API endpoints with a real database
  - Authentication endpoints
  - Task CRUD operations
  - User management
  
- **End-to-End Tests** (`tests/e2e/`): Test complete user workflows
  - User registration → login → task management
  - Multi-user scenarios
  - Error handling workflows

### Manual API Testing

1. **Test with cURL:**
   ```bash
   # Register a new user
   curl -X POST http://localhost:8000/register \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

   # Login
   curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass123"

   # Create a task (use the token from login)
   curl -X POST http://localhost:8000/tasks \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"title": "My First Task", "description": "Testing the API"}'
   ```

## Architecture Benefits

- **Separation of Concerns**: Clear boundaries between layers
- **Maintainability**: Easy to locate and modify specific functionality
- **Scalability**: Simple to add new features without affecting existing code
- **Testability**: Each layer can be tested independently
- **Dependency Injection**: Clean dependency management
- **Type Safety**: Full Pydantic model validation

## API Endpoints

### Authentication
- `POST /register` - Register a new user
  - Body: `{"username": "string", "email": "string", "password": "string"}`
- `POST /login` - Login and receive JWT token
  - Body: `username=string&password=string` (form-data)
  - Returns: `{"access_token": "string", "token_type": "bearer"}`

### User Management
- `GET /users/me` - Get current user profile (requires authentication)
  - Headers: `Authorization: Bearer <token>`

### Task Management (all require authentication)
- `GET /tasks` - List user's tasks
  - Query params: `?status=todo|in_progress|done&skip=0&limit=10`
- `POST /tasks` - Create a new task
  - Body: `{"title": "string", "description": "string", "status": "todo"}`
- `GET /tasks/{task_id}` - Get specific task
- `PUT /tasks/{task_id}` - Update task
  - Body: `{"title": "string", "description": "string", "status": "string"}`
- `DELETE /tasks/{task_id}` - Delete task

### Health Check
- `GET /health` - Application health status

## Features

- **JWT Authentication**: Secure token-based authentication
- **Task Management**: Full CRUD operations for tasks
- **User Isolation**: Each user can only access their own tasks
- **Status Filtering**: Filter tasks by status (TODO, IN_PROGRESS, DONE)
- **Pagination**: Built-in pagination for task lists
- **Input Validation**: Comprehensive request validation with Pydantic
- **Error Handling**: Consistent error responses
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

## Database

The application uses SQLite as the database, which is automatically created as `tasks.db` when you first run the application. The database includes:

- **Users table**: Stores user credentials and profile information
- **Tasks table**: Stores tasks with user association

## Development

### Test-Driven Development

The project follows TDD practices. When adding new features:

1. **Write tests first**: Start with unit tests for your logic
2. **Run tests**: Ensure they fail (red phase)
3. **Implement feature**: Write minimal code to pass tests (green phase)
4. **Refactor**: Improve code while keeping tests passing
5. **Add integration tests**: Test the complete flow

Example workflow:
```bash
# 1. Write your test
# Edit tests/unit/services/test_new_feature.py

# 2. Run the test (should fail)
pytest tests/unit/services/test_new_feature.py

# 3. Implement the feature
# Edit app/services/new_feature.py

# 4. Run tests again (should pass)
pytest tests/unit/services/test_new_feature.py

# 5. Run all tests to ensure nothing broke
pytest

# 6. Check coverage
pytest --cov=app --cov-report=term-missing
```

### Project Layout

The application follows a clean architecture pattern with clear separation between:

- **API Layer** (`app/api/`): HTTP endpoints and request/response handling
- **Core Layer** (`app/core/`): Business rules, middleware, and cross-cutting concerns
- **Database Layer** (`app/db/`): Data persistence and ORM models
- **Models Layer** (`app/models/`): Data transfer objects (DTOs)
- **Services Layer** (`app/services/`): Business logic and domain services
- **Utils Layer** (`app/utils/`): Shared utilities and constants

### Adding New Features

1. **New Endpoint**: Add router in `app/api/routers/`
2. **New Model**: Add Pydantic model in `app/models/`
3. **New Service**: Add business logic in `app/services/`
4. **New Database Model**: Add SQLAlchemy model in `app/db/models.py`
5. **Write Tests**: Add tests in appropriate `tests/` subdirectory

### Continuous Integration

The project includes GitHub Actions workflow for automated testing:

- Runs on every push and pull request
- Executes all test categories (unit, integration, e2e)
- Generates coverage reports
- Fails if coverage drops below 80%
- Uploads coverage to Codecov (if configured)

To run tests locally before pushing:
```bash
# Run the same checks as CI
make test
make lint  # If linting is configured
```

## License

This project is open source and available under the MIT License.



Advanced Task Management System Expansion Plan

     Phase 1: Core Task Enhancements (Week 1-2)

     1. Enhanced Task Properties
       - Add priority levels (LOW, MEDIUM, HIGH, URGENT)
       - Add due_date and start_date fields
       - Add estimated_hours and actual_hours for time tracking
       - Add completed_at timestamp
       - Add task position for manual ordering
     2. Categories and Tags
       - Create Category model (many-to-many with tasks)
       - Create Tag model with color support
       - Add endpoints for managing categories/tags
       - Enable filtering by categories/tags
     3. Subtasks and Dependencies
       - Add parent_task_id for subtask relationships
       - Create TaskDependency model
       - Add validation to prevent circular dependencies
       - Update task completion logic for dependencies

     Phase 2: Collaboration Features (Week 3-4)

     1. Team/Project Management
       - Create Project model with members
       - Add role-based permissions (OWNER, ADMIN, MEMBER, VIEWER)
       - Create project invitation system
       - Update task model to support project assignment
     2. Task Assignment and Sharing
       - Add assigned_to field for task delegation
       - Create TaskShare model for sharing individual tasks
       - Add notification system for assignments
       - Implement activity feed for task changes
     3. Comments and Attachments
       - Create Comment model with @mention support
       - Create Attachment model with file metadata
       - Integrate with cloud storage (S3/MinIO)
       - Add file upload endpoints with validation

     Phase 3: Advanced Features (Week 5-6)

     1. Recurring Tasks
       - Create RecurrenceRule model
       - Add task template system
       - Implement background job for creating recurring instances
       - Add endpoints for managing recurring tasks
     2. Notifications and Reminders
       - Create Notification model and preferences
       - Implement email notification service
       - Add in-app notification system
       - Create reminder scheduling with Celery
     3. Advanced Search and Filtering
       - Implement full-text search with PostgreSQL
       - Add advanced filter combinations
       - Create saved filter/view system
       - Add bulk operations endpoints

     Phase 4: Analytics and Integration (Week 7-8)

     1. Analytics Dashboard
       - Create analytics service for metrics
       - Add productivity statistics endpoints
       - Implement time tracking reports
       - Create export functionality (CSV/Excel)
     2. External Integrations
       - Add webhook system for events
       - Create calendar sync endpoints
       - Implement OAuth for Google/Microsoft
       - Add API versioning
     3. Performance Optimization
       - Migrate to PostgreSQL
       - Implement Redis caching
       - Add database indexing strategy
       - Optimize query performance

     Technical Implementation Details:

     New Models to Create:
     - Priority, Category, Tag, Project, ProjectMember
     - TaskDependency, TaskShare, Comment, Attachment
     - RecurrenceRule, TaskTemplate, Notification
     - UserPreference, WebhookSubscription, AuditLog

     New Services:
     - ProjectService, NotificationService, FileService
     - AnalyticsService, RecurrenceService, SearchService
     - IntegrationService, ExportService

     Infrastructure Changes:
     - PostgreSQL migration for better performance
     - Redis for caching and session management
     - Celery + Redis for background jobs
     - MinIO/S3 for file storage
     - Email service (SendGrid/AWS SES)

     API Enhancements:
     - Versioned API (v1, v2)
     - GraphQL endpoint option
     - WebSocket support for real-time updates
     - Batch operation endpoints
     - Enhanced error handling and validation

     Security Improvements:
     - Two-factor authentication
     - API rate limiting
     - Role-based access control
     - Audit logging
     - Data encryption for sensitive fields

     This plan transforms the basic task manager into a full-featured, enterprise-ready task management system while maintaining the clean architecture and high test coverage standards.


Update Todos
⎿  ☒ Create enhanced task properties (priority, dates, time tracking)
    ☒ Implement categories and tags system
    ☒ Set up production-grade migration system with Alembic
    ☒ Add subtasks and task dependencies
    ☒ Write unit tests for TaskDependencyService
    ☒ Write integration tests for task dependency API endpoints
    ☐ Create project/team management models
    ☐ Implement task assignment and sharing
    ☐ Add comments and @mentions system
    ☐ Create file attachment functionality
    ☐ Implement recurring tasks system
    ☐ Add notification and reminder system
    ☐ Create advanced search and filtering
    ☐ Build analytics and reporting features
    ☐ Add external integrations (webhooks, calendar)
    ☐ Migrate to PostgreSQL
    ☐ Set up Redis caching
    ☐ Configure Celery for background jobs

