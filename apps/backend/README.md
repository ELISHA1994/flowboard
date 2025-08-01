# Task Management Backend API

A robust, scalable FastAPI backend for task management with clean architecture, comprehensive testing, and advanced features.

## =� Features

### Core Features

- **JWT Authentication**: Secure token-based authentication with bcrypt password hashing
- **Task Management**: Full CRUD operations with status tracking and priorities
- **Project Management**: Team collaboration with role-based permissions
- **Advanced Search**: Complex filtering with saved searches and bulk operations
- **Analytics**: Comprehensive reporting and time tracking
- **Background Jobs**: Celery-powered async task processing
- **Caching**: Redis integration for performance optimization
- **Real-time Updates**: Webhook system for external integrations

### Technical Features

- **Clean Architecture**: Clear separation of concerns between layers
- **Type Safety**: Pydantic models for request/response validation
- **Database Migrations**: Alembic for version-controlled schema changes
- **Comprehensive Testing**: 100% test coverage with unit, integration, and E2E tests
- **API Documentation**: Auto-generated Swagger/OpenAPI docs
- **Error Handling**: Consistent error responses with custom exceptions
- **Logging**: Structured logging with request tracking

## =� Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and message broker
- **Background Jobs**: Celery with Redis broker
- **Authentication**: JWT tokens with python-jose
- **Testing**: pytest with factories and fixtures
- **Documentation**: OpenAPI/Swagger

## =� Project Structure

```
apps/backend/
   app/
      api/                # API layer
         main.py        # Router aggregator
         endpoints/     # Additional endpoints
         routers/       # Route modules
      core/              # Core components
         config.py      # Configuration
         auth.py        # Authentication
         exceptions.py  # Custom exceptions
         logging.py     # Logging setup
      db/                # Database layer
         database.py    # Connection setup
         models.py      # SQLAlchemy models
      models/            # Pydantic DTOs
      services/          # Business logic
      tasks/             # Celery tasks
      utils/             # Utilities
   migrations/            # Alembic migrations
   scripts/               # Utility scripts
   tests/                 # Test suite
      unit/             # Unit tests
      integration/      # Integration tests
      e2e/              # End-to-end tests
      factories/        # Test data factories
   requirements.txt       # Python dependencies
```

## =� Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Virtual environment tool (venv, virtualenv, etc.)

### Development Setup

#### From Monorepo Root (Recommended)

```bash
# Install dependencies
pnpm install

# Start with Docker
pnpm docker:up

# Run migrations
docker-compose exec backend alembic upgrade head

# Start development server
pnpm dev:backend
```

#### Manual Setup (from apps/backend/)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up databases
python scripts/setup_postgres.py

# Run migrations
alembic upgrade head

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the server
uvicorn app.main:app --reload --log-level info
```

### Testing

```bash
# From monorepo root
pnpm test:backend

# Or from backend directory
make test           # All tests with coverage
make test-unit      # Unit tests only
make test-integration  # Integration tests
make test-e2e       # End-to-end tests
make coverage       # Generate HTML coverage report
```

## =' Configuration

### Environment Variables

Create `.env` file in `apps/backend/`:

```env
# JWT Configuration
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DB_HOST=localhost
DB_NAME=taskmanager
DB_USER=taskmanageruser
DB_PASSWORD=taskmanagerpass
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=.jpg,.jpeg,.png,.pdf,.doc,.docx
```

## =� API Endpoints

### Authentication

- `POST /register` - Create new account
- `POST /login` - Authenticate and get JWT token
- `GET /users/me` - Get current user profile

### Tasks

- `GET /tasks` - List tasks with filtering
- `POST /tasks` - Create new task
- `GET /tasks/{id}` - Get specific task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

### Projects

- `GET /projects` - List user's projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `POST /projects/{id}/members` - Add team member

### Search & Analytics

- `POST /search/tasks` - Advanced search
- `GET /analytics/statistics` - Task statistics
- `POST /analytics/export` - Export data

[Full API documentation available at http://localhost:8000/docs]

## >� Testing

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - All dependencies mocked
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Test API endpoints with real database
   - Validate request/response flow
   - Test authentication and permissions

3. **E2E Tests** (`tests/e2e/`)
   - Test complete user workflows
   - Multi-step operations
   - Real-world scenarios

### Running Tests

```bash
# Specific test file
pytest tests/unit/services/test_task_service.py

# With coverage
pytest --cov=app --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

## =� Background Jobs (Celery)

### Starting Celery

```bash
# Start all components
./scripts/celery/start_all.sh

# Individual components
./scripts/celery/start_worker.sh
./scripts/celery/start_beat.sh

# Monitor tasks
./scripts/celery/monitor.sh watch
```

### Available Queues

- `default` - General tasks
- `notifications` - Email/push notifications
- `recurring` - Recurring task processing
- `webhooks` - Webhook deliveries
- `analytics` - Report generation
- `reminders` - Task reminders

## =

Debugging

### Enable Debug Logging

```python
# In .env
LOG_LEVEL=DEBUG

# Or when starting server
uvicorn app.main:app --log-level debug
```

### Request Logging

All requests are logged with:

- Method and path
- Status code
- Response time
- User ID (if authenticated)

Example:

```
2025-01-20 19:45:12,123 - app.main - INFO - =5 POST /login
2025-01-20 19:45:12,256 - app.main - INFO -  POST /login - 200 - 0.133s
```

### Common Issues

1. **CORS Errors**: Check `allow_origins` in `app/main.py`
2. **Database Connection**: Verify PostgreSQL is running and credentials are correct
3. **Redis Connection**: Ensure Redis is running on configured port
4. **Import Errors**: Activate virtual environment before running

## =� Performance

### Caching Strategy

The `@cached` decorator is used for frequently accessed data:

```python
@cached(prefix="user", ttl=300)
def get_user_by_id(db: Session, user_id: str):
    # Cached for 5 minutes
```

� **Note**: Avoid caching methods with complex objects containing enums.

### Database Optimization

- Connection pooling enabled
- Indexed columns for common queries
- Eager loading for related data
- Pagination on all list endpoints

## = Security

- Password hashing with bcrypt
- JWT tokens with expiration
- SQL injection prevention via ORM
- Input validation with Pydantic
- File upload restrictions
- CORS configuration
- Rate limiting (planned)

## =� Development Guidelines

1. **Service Layer Pattern**: Business logic in services, not endpoints
2. **Dependency Injection**: Use FastAPI's `Depends()` for dependencies
3. **Error Handling**: Raise custom exceptions, handle in middleware
4. **Testing**: Write tests first (TDD approach)
5. **Type Hints**: Use type hints everywhere
6. **Docstrings**: Document all public methods

## > Contributing

1. Create feature branch from `main`
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation
5. Follow commit conventions
6. Submit pull request

## =� License

This project is part of the Task Management System monorepo.
