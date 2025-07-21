# Task Management System - Monorepo

A modern full-stack task management system built as a monorepo. Features a FastAPI backend with clean architecture principles and a Next.js frontend with modern UI/UX. Includes JWT authentication, PostgreSQL database, Redis caching, Celery background tasks, and comprehensive task management capabilities.

> **Note for Existing Users**: This repository has been converted to a monorepo structure. The backend code is now located in `apps/backend/`. All existing functionality remains the same, but the development workflow has been improved with Turborepo and pnpm workspaces.
>
> **Migration Guide**: If you have an existing clone:
>
> 1. Pull the latest changes: `git pull`
> 2. Install pnpm: `npm install -g pnpm`
> 3. Install dependencies: `pnpm install`
> 4. Update your scripts to use the new commands (see below)

## 🏗️ Why Monorepo?

This project uses a monorepo structure with **pnpm workspaces** and **Turborepo** for several benefits:

- **🚀 Unified Development**: Single repository for backend and future frontend
- **⚡ Optimized Builds**: Turborepo provides intelligent caching and parallel execution
- **📦 Shared Dependencies**: Common packages and types shared across applications
- **🔄 Atomic Changes**: Backend and frontend changes can be made in the same commit
- **🛠️ Consistent Tooling**: Shared linting, formatting, and build configurations
- **💾 Efficient Storage**: pnpm's content-addressable storage saves disk space

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)

```bash
# Clone and setup everything
git clone <repository-url>
cd task-management-monorepo
./setup.sh

# That's it! Services are running at:
# - API Documentation: http://localhost:8000/docs
# - Flower (Celery UI): http://localhost:5555
```

### Option 2: Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd task-management-monorepo

# Install pnpm and dependencies
npm install -g pnpm
pnpm install

# Start all services with Docker
pnpm docker:up

# Run database migrations
docker-compose exec backend alembic upgrade head

# View logs
pnpm docker:logs
```

### Option 3: Manual Setup

```bash
# Clone the repository
git clone <repository-url>
cd task-management-monorepo

# Install pnpm (if not already installed)
npm install -g pnpm

# Install dependencies
pnpm install

# Backend setup
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set up PostgreSQL and Redis (must be installed locally)
python scripts/setup_postgres.py
alembic upgrade head

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Return to root and start services
cd ../..
pnpm dev:backend  # Backend only
# OR
pnpm dev         # All services
```

## 📁 Monorepo Structure

```
task-management-monorepo/
├── apps/
│   ├── backend/              # FastAPI backend application
│   │   ├── app/             # Application source code
│   │   │   ├── api/         # API endpoints and routing
│   │   │   ├── core/        # Core components (config, auth, logging)
│   │   │   ├── db/          # Database models and connection
│   │   │   ├── models/      # Pydantic DTOs
│   │   │   ├── services/    # Business logic layer
│   │   │   ├── tasks/       # Celery background tasks
│   │   │   └── utils/       # Utilities
│   │   ├── tests/           # Test suite
│   │   ├── scripts/         # Utility scripts
│   │   ├── migrations/      # Database migrations
│   │   ├── requirements.txt # Python dependencies
│   │   ├── Dockerfile       # Production Docker image
│   │   └── package.json     # NPM scripts for Turborepo
│   └── web/                 # Next.js frontend application
│       ├── app/             # Next.js App Router pages
│       ├── components/      # React components
│       │   ├── ui/          # shadcn/ui components
│       │   └── layouts/     # Layout components
│       ├── lib/             # Utilities and helpers
│       └── public/          # Static assets
├── packages/
│   ├── types/               # Shared TypeScript types (future)
│   ├── ui/                  # Shared UI components (future)
│   └── config/              # Shared configurations (future)
├── docker-compose.yml       # Local development environment
├── turbo.json              # Turborepo configuration
├── pnpm-workspace.yaml     # pnpm workspace configuration
└── package.json            # Root package scripts
```

## 🛠️ Technology Stack

### Backend (FastAPI)

- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and Celery broker
- **Authentication**: JWT tokens with bcrypt password hashing
- **Background Tasks**: Celery with scheduled tasks
- **API Documentation**: Auto-generated OpenAPI/Swagger

### Frontend (Next.js)

- **Framework**: Next.js 15.4+ with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS v4 with CSS-first approach
- **UI Components**: shadcn/ui + Radix UI primitives
- **State Management**: React Context (auth), Zustand (global state - planned)
- **Forms**: React Hook Form with Zod validation (planned)
- **Authentication**: JWT-based with protected routes
- **Dark Mode**: Built-in theme support with system preference detection
- **Icons**: Lucide React

### Infrastructure

- **Monorepo Tool**: Turborepo for build optimization
- **Package Manager**: pnpm for efficient dependency management
- **Containerization**: Docker & Docker Compose
- **Development**: Hot reloading with volume mounts
- **Git Hooks**: Husky for pre-commit and commit-msg hooks
- **Code Quality**: commitlint for conventional commits, lint-staged for pre-commit checks

## 🎯 Monorepo Commands

All commands should be run from the repository root directory:

### Development Commands

```bash
# Start services
pnpm dev                 # Start all services (backend + frontend)
pnpm dev:backend        # Start only backend service
pnpm dev:web           # Start only frontend service

# Docker management
pnpm docker:up         # Start all services with Docker Compose
pnpm docker:down       # Stop all Docker services
pnpm docker:logs       # View real-time logs from all services
```

### Testing Commands

```bash
# Run tests
pnpm test              # Run all tests across the monorepo
pnpm test:backend      # Run only backend tests

# Backend-specific test commands (must cd to apps/backend/ first)
cd apps/backend
make test              # Run all backend tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-e2e         # Run end-to-end tests only
make coverage          # Generate test coverage report

# OR use pnpm filters from root (no cd needed)
pnpm --filter @taskman/backend exec make test
pnpm --filter @taskman/backend exec make coverage
```

### Code Quality Commands

```bash
# From monorepo root
pnpm lint              # Lint all code in the monorepo
pnpm format            # Auto-format all code
pnpm type-check        # Run TypeScript type checking

# Backend-specific (must cd to apps/backend/ first)
cd apps/backend
make lint              # Run Python linters (black, flake8, mypy)
make format            # Format Python code with black and isort

# OR use pnpm filters from root (no cd needed)
pnpm --filter @taskman/backend exec make lint
pnpm --filter @taskman/backend exec make format
```

### Build & Deployment Commands

```bash
# Building
pnpm build             # Build all applications
pnpm clean             # Clean all build artifacts and caches

# Type generation
pnpm generate:types    # Generate TypeScript types from FastAPI OpenAPI schema
```

### Backend-Specific Commands

These commands **must be run from the `apps/backend/` directory**:

```bash
# First, navigate to the backend directory
cd apps/backend

# Database operations
make migrate           # Run database migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Python environment setup
python -m venv .venv   # Create virtual environment
source .venv/bin/activate  # Activate virtual environment (Windows: .venv\Scripts\activate)
pip install -r requirements.txt  # Install Python dependencies

# Running tests from backend directory
make test              # Run all backend tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make coverage          # Generate coverage report

# Code quality from backend directory
make lint              # Run Python linters
make format            # Format Python code

# Celery (Background Tasks) - also from apps/backend/
# For macOS users - use the following commands to avoid fork safety issues:
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # Required for macOS
celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo  # Single process worker

# OR use the provided scripts (also from apps/backend/):
./scripts/celery/start_all.sh    # Start all Celery components
./scripts/celery/start_worker.sh  # Start Celery worker only
./scripts/celery/start_beat.sh    # Start Celery beat scheduler
./scripts/celery/monitor.sh watch # Monitor Celery tasks
```

**Alternative**: You can also run backend commands from the root using pnpm filters:

```bash
# From monorepo root - no need to cd into backend
pnpm --filter @taskman/backend test
pnpm --filter @taskman/backend lint
pnpm --filter @taskman/backend migrate
```

### Troubleshooting Commands

```bash
# Clear caches
pnpm clean             # Clear all build caches
rm -rf .turbo          # Clear Turborepo cache
rm -rf node_modules    # Clear node_modules (then run pnpm install)

# Check service status
docker-compose ps      # Check Docker container status
docker-compose logs backend -f  # View backend logs
docker-compose logs postgres -f # View database logs

# Database operations
docker-compose exec backend alembic history  # View migration history
docker-compose exec backend alembic current  # Check current migration
docker-compose exec postgres psql -U taskmanageruser -d taskmanager  # Access database
```

## 📚 Backend Project Structure

```
apps/backend/app/
├── api/                 # API endpoints and routing
│   ├── main.py         # Main API router aggregator
│   ├── endpoints/      # Additional endpoint modules
│   │   └── projects.py # Project management endpoints
│   └── routers/        # Individual route modules
│       ├── analytics.py     # Analytics and reporting endpoints
│       ├── auth.py          # Authentication endpoints
│       ├── calendar.py      # Calendar integration endpoints
│       ├── categories.py    # Category management endpoints
│       ├── comments.py      # Comment system endpoints
│       ├── files.py         # File attachment endpoints
│       ├── notifications.py # Notification endpoints
│       ├── search.py        # Advanced search endpoints
│       ├── tags.py          # Tag management endpoints
│       ├── tasks.py         # Task CRUD endpoints
│       ├── users.py         # User profile endpoints
│       └── webhooks.py      # Webhook subscription endpoints
├── core/               # Core application components
│   ├── celery_app.py   # Celery configuration
│   ├── config.py       # Application configuration
│   ├── exception_handlers.py  # Global exception handling
│   ├── exceptions.py   # Custom exception classes
│   ├── logging.py      # Logging configuration
│   ├── middleware/     # Middleware components
│   │   └── jwt_auth_backend.py  # JWT authentication
│   └── models.py       # Core response models
├── db/                 # Database layer
│   ├── database.py     # Database connection setup
│   ├── db_instance.py  # Database dependency injection
│   └── models.py       # SQLAlchemy ORM models (all entities)
├── models/             # Pydantic models (DTOs)
│   ├── analytics.py    # Analytics request/response models
│   ├── calendar.py     # Calendar integration models
│   ├── category.py     # Category models
│   ├── comment.py      # Comment models
│   ├── file_attachment.py  # File attachment models
│   ├── notification.py # Notification models
│   ├── project.py      # Project models
│   ├── search.py       # Search and filter models
│   ├── tag.py          # Tag models
│   ├── task.py         # Task request/response models
│   ├── user.py         # User request/response models
│   └── webhook.py      # Webhook models
├── services/           # Business logic layer
│   ├── analytics_service.py      # Analytics computation
│   ├── bulk_operations_service.py # Bulk task operations
│   ├── cache_service.py          # Redis caching service
│   ├── calendar_service.py       # Calendar integration
│   ├── category_service.py       # Category management
│   ├── comment_service.py        # Comment system logic
│   ├── file_service.py           # File handling
│   ├── notification_service.py   # Notification logic
│   ├── project_service.py        # Project management
│   ├── recurrence_service.py     # Recurring task logic
│   ├── search_service.py         # Advanced search logic
│   ├── tag_service.py            # Tag management
│   ├── task_dependency_service.py # Task dependencies
│   ├── task_service.py           # Task-related business logic
│   ├── user_service.py           # User-related business logic
│   └── webhook_service.py        # Webhook delivery logic
├── tasks/              # Celery background tasks
│   ├── analytics.py    # Analytics computation tasks
│   ├── notifications.py # Notification sending tasks
│   ├── recurring.py    # Recurring task processing
│   ├── reminders.py    # Reminder tasks
│   └── webhooks.py     # Webhook delivery tasks
├── utils/              # Utilities and constants
│   └── constants.py    # Application constants
└── main.py            # FastAPI application entry point

migrations/             # Alembic database migrations
├── alembic.ini        # Alembic configuration
├── env.py             # Migration environment setup
├── script.py.mako     # Migration template
└── versions/          # Migration files

scripts/               # Utility scripts
├── celery/            # Celery management scripts
│   ├── start_all.sh   # Start all Celery components
│   ├── start_worker.sh # Start individual worker
│   ├── start_beat.sh  # Start beat scheduler
│   └── monitor.sh     # Monitor Celery tasks
├── setup_postgres.py  # PostgreSQL setup script
├── test_celery.py     # Test Celery configuration
├── test_redis_cache.py # Test Redis connection
└── test_async_integration.py # Test async components

tests/                  # Comprehensive test suite
├── unit/              # Unit tests (isolated, mocked)
├── integration/       # Integration tests (with database)
├── e2e/              # End-to-end workflow tests
├── factories/        # Test data factories
└── conftest.py       # Shared pytest fixtures

docs/                  # Documentation
├── CELERY_INTEGRATION.md  # Celery integration guide
└── API_DOCUMENTATION.md   # Detailed API docs
```

## 💡 Working with the Monorepo

### Adding Dependencies

```bash
# Add a dependency to the backend
pnpm --filter @taskman/backend add <package-name>

# Add a dev dependency to the root
pnpm add -D -w <package-name>

# Add Python dependencies (from apps/backend/)
cd apps/backend
pip install <package-name>
pip freeze > requirements.txt
```

### Running Commands in Specific Workspaces

```bash
# Run any command in a specific workspace
pnpm --filter @taskman/backend <command>

# Examples:
pnpm --filter @taskman/backend test
pnpm --filter @taskman/backend generate:schema
```

### Environment Variables

1. **For Docker Development**: Environment variables are set in `docker-compose.yml`
2. **For Local Development**: Create `.env` file in `apps/backend/`:
   ```bash
   cd apps/backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Common Development Workflows

#### Starting Fresh

```bash
./setup.sh  # Installs everything and starts services
```

#### Daily Development

```bash
pnpm docker:up    # Start services
pnpm dev:backend  # Start backend with hot reload
pnpm docker:logs  # Monitor logs in another terminal
```

#### Running Tests

```bash
pnpm test:backend  # Quick test run
cd apps/backend && make coverage  # Detailed coverage report
```

#### Database Changes

```bash
# Create a new migration
cd apps/backend
alembic revision --autogenerate -m "add new feature"
alembic upgrade head  # Apply migration

# With Docker
docker-compose exec backend alembic revision --autogenerate -m "add new feature"
docker-compose exec backend alembic upgrade head
```

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose (for containerized development)
- PostgreSQL 15+ (for local development without Docker)
- Redis 7+ (for local development without Docker)

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
   pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic
   pip install python-jose[cryptography] bcrypt python-multipart
   pip install email-validator python-dotenv pydantic[email]
   pip install redis celery[redis] flower
   pip install aiofiles pandas openpyxl

   # Test dependencies
   pip install pytest pytest-asyncio pytest-cov httpx factory-boy faker
   pip install pytest-mock freezegun
   ```

## Database Setup

### PostgreSQL Setup

1. **Install PostgreSQL:**
   - macOS: `brew install postgresql`
   - Ubuntu/Debian: `sudo apt-get install postgresql postgresql-contrib`
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/)

2. **Create database and user:**

   ```bash
   # Access PostgreSQL prompt
   sudo -u postgres psql

   # Create user and databases
   CREATE USER taskmanageruser WITH PASSWORD 'taskmanagerpass';
   CREATE DATABASE taskmanager OWNER taskmanageruser;
   CREATE DATABASE taskmanager_test OWNER taskmanageruser;
   \q
   ```

3. **Run setup script:**

   ```bash
   python scripts/setup_postgres.py
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

### Redis Setup (Required for Caching and Background Jobs)

1. **Install Redis:**
   - macOS: `brew install redis`
   - Ubuntu/Debian: `sudo apt-get install redis-server`
   - Windows: Download from [redis.io](https://redis.io/download)

2. **Start Redis server:**

   ```bash
   # macOS/Linux
   redis-server

   # Or as a service
   sudo systemctl start redis
   ```

3. **Test Redis connection:**
   ```bash
   python scripts/test_redis_cache.py
   ```

### Celery Setup (Background Job Processing)

Celery is used for processing background tasks like sending notifications, processing recurring tasks, and generating analytics reports.

#### macOS-Specific Setup

If you're on macOS, you'll need to use special settings to avoid fork safety issues:

```bash
# Required environment variable for macOS
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Start Celery with solo pool (single process)
cd apps/backend
celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo

# For debugging, use debug log level
celery -A app.core.celery_app:celery_app worker --loglevel=debug --pool=solo
```

#### Standard Setup (Linux/Windows/Docker)

1. **Test Celery Configuration:**

   ```bash
   python scripts/test_celery.py
   ```

2. **Start Celery Workers:**

   **Option 1 - Start all infrastructure (recommended):**

   ```bash
   # Start workers, beat scheduler, and optional monitoring
   ./scripts/celery/start_all.sh

   # With custom settings
   ./scripts/celery/start_all.sh --workers 4 --concurrency 8 --monitor

   # Check status
   ./scripts/celery/start_all.sh --status

   # Stop all
   ./scripts/celery/start_all.sh --stop
   ```

   **Option 2 - Start components individually:**

   ```bash
   # Start a worker
   ./scripts/celery/start_worker.sh

   # Start beat scheduler (for periodic tasks)
   ./scripts/celery/start_beat.sh

   # Monitor tasks
   ./scripts/celery/monitor.sh watch
   ```

3. **Celery Commands:**

   ```bash
   # Start worker with custom options
   ./scripts/celery/start_worker.sh -n worker1 -c 4 -l info -q default,notifications

   # Start beat scheduler with custom log level
   ./scripts/celery/start_beat.sh -l debug

   # Monitor commands
   ./scripts/celery/monitor.sh status      # Show worker status
   ./scripts/celery/monitor.sh inspect     # Inspect workers and queues
   ./scripts/celery/monitor.sh stats       # Show statistics
   ./scripts/celery/monitor.sh active      # Show active tasks
   ./scripts/celery/monitor.sh watch       # Continuous monitoring
   ```

4. **Available Task Queues:**
   - `default` - General purpose tasks
   - `notifications` - Email and in-app notifications
   - `recurring` - Processing recurring tasks
   - `webhooks` - Webhook deliveries
   - `analytics` - Analytics computation and reports
   - `reminders` - Task reminders and summaries

5. **Periodic Tasks:**
   The following tasks run automatically when beat scheduler is active:
   - Process recurring tasks (every 5 minutes)
   - Send reminder notifications (every 15 minutes)
   - Cleanup expired notifications (every hour)
   - Precompute analytics cache (every 30 minutes)

## Configuration

1. **Environment Variables:**
   Create a `.env` file in the project root:

   ```env
   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Database Configuration
   DB_HOST=127.0.0.1
   DB_NAME=taskmanager
   DB_USER=taskmanageruser
   DB_PASSWORD=taskmanagerpass
   DB_PORT=5432

   # Redis Configuration (Required for caching and background jobs)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=
   REDIS_DEFAULT_TTL=300
   REDIS_MAX_CONNECTIONS=10

   # Celery Configuration
   CELERY_BROKER_URL=  # Defaults to Redis URL
   CELERY_RESULT_BACKEND=  # Defaults to Redis URL
   CELERY_TASK_SERIALIZER=json
   CELERY_RESULT_SERIALIZER=json
   CELERY_ACCEPT_CONTENT=json
   CELERY_TIMEZONE=UTC
   CELERY_ENABLE_UTC=True
   CELERY_WORKER_PREFETCH_MULTIPLIER=4
   CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
   CELERY_TASK_ALWAYS_EAGER=False  # Set to True for testing without worker
   CELERY_RESULT_EXPIRES=3600

   # Background Task Intervals (in seconds)
   RECURRING_TASK_CHECK_INTERVAL=300  # 5 minutes
   REMINDER_CHECK_INTERVAL=900  # 15 minutes
   NOTIFICATION_CLEANUP_INTERVAL=3600  # 1 hour
   ANALYTICS_CACHE_INTERVAL=1800  # 30 minutes

   # File Upload Configuration
   UPLOAD_DIR=uploads
   MAX_FILE_SIZE=10485760  # 10MB in bytes
   ALLOWED_FILE_TYPES=.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.csv,.xlsx,.xls,.zip
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

## 🌐 Available Services

When running with Docker (`pnpm docker:up` or `./setup.sh`):

| Service              | URL                         | Description                                  |
| -------------------- | --------------------------- | -------------------------------------------- |
| **Next.js Frontend** | http://localhost:3000       | Modern React-based user interface            |
| **FastAPI Backend**  | http://localhost:8000       | Main API server                              |
| **Swagger UI**       | http://localhost:8000/docs  | Interactive API documentation                |
| **ReDoc**            | http://localhost:8000/redoc | Alternative API documentation                |
| **Flower**           | http://localhost:5555       | Celery task monitoring UI                    |
| **PostgreSQL**       | localhost:5432              | Database (credentials in docker-compose.yml) |
| **Redis**            | localhost:6379              | Cache and message broker                     |

### Health Checks

- API Health: http://localhost:8000/health
- All services include Docker health checks for automatic recovery

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
  - Query params: `?status=todo|in_progress|done&priority=low|medium|high|urgent&assigned_to_id=string&project_id=string&skip=0&limit=10`
- `POST /tasks` - Create a new task
  - Body: `{"title": "string", "description": "string", "status": "todo", "priority": "medium", "assigned_to_id": "string"}`
- `GET /tasks/{task_id}` - Get specific task
- `PUT /tasks/{task_id}` - Update task
  - Body: `{"title": "string", "description": "string", "status": "string", "assigned_to_id": "string"}`
- `DELETE /tasks/{task_id}` - Delete task
- `POST /tasks/{task_id}/time` - Log time to task
  - Body: `{"hours_to_add": 2.5}`
- `GET /tasks/project/{project_id}` - Get all tasks in a project

### Task Sharing

- `POST /tasks/{task_id}/share` - Share a task with another user
  - Body: `{"task_id": "string", "shared_with_id": "string", "permission": "view|edit|comment"}`
- `GET /tasks/shared/with-me` - Get tasks shared with you
- `DELETE /tasks/{task_id}/share/{share_id}` - Remove a task share

### Advanced Search and Filtering

- `POST /search/tasks` - Advanced task search with filters
  - Body: `{"text": "search term", "filters": [{"field": "status", "operator": "eq", "value": "todo"}], "sort_by": "created_at", "sort_order": "desc", "skip": 0, "limit": 20}`
  - Supported operators: eq, ne, gt, gte, lt, lte, contains, not_contains, in, not_in, is_null, is_not_null
  - Filterable fields: title, description, status, priority, due_date, start_date, completed_at, created_at, updated_at, estimated_hours, actual_hours, assigned_to, project, is_recurring, has_subtasks
- `GET /search/suggestions` - Get search filter suggestions
- `POST /search/bulk` - Perform bulk operations on tasks
  - Body: `{"task_ids": ["id1", "id2"], "operation": "update_status", "value": "done"}`
  - Operations: update_status, update_priority, update_assigned_to, add_tags, remove_tags, add_categories, remove_categories, delete, move_to_project
- `POST /search/saved` - Create a saved search
- `GET /search/saved` - Get all saved searches
- `GET /search/saved/{search_id}` - Get specific saved search
- `PUT /search/saved/{search_id}` - Update saved search
- `DELETE /search/saved/{search_id}` - Delete saved search

### Analytics and Reporting

- `POST /analytics/tasks/{task_id}/time-log` - Log time to a task
  - Body: `{"hours": 2.5, "description": "Worked on implementation", "logged_at": "2024-01-20T10:00:00Z"}`
- `GET /analytics/statistics` - Get task statistics
  - Query params: `?start_date=2024-01-01&end_date=2024-01-31&project_id=proj1`
  - Returns: total tasks, status/priority breakdowns, completion rate, average completion time, overdue tasks
- `GET /analytics/productivity-trends` - Get productivity trends over time
  - Query params: `?period=week&lookback=4` (period: week/month/quarter)
  - Returns: tasks created/completed and hours logged per period
- `POST /analytics/time-tracking/report` - Get time tracking report
  - Body: `{"start_date": "2024-01-01", "end_date": "2024-01-31", "group_by": "task"}`
  - Group by options: task, project, category, day
- `GET /analytics/category-distribution` - Get task distribution by categories
  - Query params: `?project_id=proj1`
- `GET /analytics/tag-distribution` - Get task distribution by tags
  - Query params: `?project_id=proj1`
- `GET /analytics/team-performance/{project_id}` - Get team performance metrics
  - Returns: tasks assigned/completed and hours logged per team member
- `POST /analytics/export` - Export tasks to CSV or Excel
  - Body: `{"format": "csv", "task_ids": ["id1", "id2"]}` (format: csv/excel)

### Categories and Tags

- `GET /categories` - List user's categories
- `POST /categories` - Create a new category
  - Body: `{"name": "string", "color": "#FF5733", "description": "string"}`
- `PUT /categories/{category_id}` - Update category
- `DELETE /categories/{category_id}` - Delete category
- `GET /tags` - List user's tags
- `POST /tags` - Create a new tag
  - Body: `{"name": "string", "color": "#FF5733"}`
- `PUT /tags/{tag_id}` - Update tag
- `DELETE /tags/{tag_id}` - Delete tag

### Comments and Mentions

- `GET /tasks/{task_id}/comments` - Get task comments
  - Query params: `?include_replies=true`
- `POST /tasks/{task_id}/comments` - Add comment to task
  - Body: `{"content": "string", "parent_comment_id": "string"}`
- `PUT /comments/{comment_id}` - Update comment
- `DELETE /comments/{comment_id}` - Delete comment
- `GET /users/me/mentions` - Get comments where user is mentioned
  - Query params: `?skip=0&limit=20`

### File Attachments

- `POST /tasks/{task_id}/files` - Upload file to task
  - Form data with file upload
- `GET /tasks/{task_id}/files` - List task attachments
- `GET /files/{file_id}` - Download file
- `DELETE /files/{file_id}` - Delete file attachment

### Projects

- `GET /projects` - List user's projects
- `POST /projects` - Create a new project
  - Body: `{"name": "string", "description": "string", "color": "#FF5733"}`
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project
- `GET /projects/{project_id}/members` - List project members
- `POST /projects/{project_id}/members` - Add project member
  - Body: `{"user_id": "string", "role": "MEMBER"}`
- `PUT /projects/{project_id}/members/{user_id}` - Update member role
- `DELETE /projects/{project_id}/members/{user_id}` - Remove member

### Task Dependencies and Subtasks

- `POST /tasks/{task_id}/dependencies` - Add task dependency
  - Body: `{"depends_on_id": "string"}`
- `GET /tasks/{task_id}/dependencies` - Get task dependencies
- `DELETE /tasks/{task_id}/dependencies/{depends_on_id}` - Remove dependency
- `POST /tasks/{task_id}/subtasks` - Create subtask
  - Body: Same as task creation, automatically sets parent_task_id
- `GET /tasks/{task_id}/subtasks` - Get task's subtasks

### Recurring Tasks

- `POST /tasks/{task_id}/recurrence` - Set task recurrence
  - Body: `{"pattern": "daily|weekly|monthly|yearly", "interval": 1, "days_of_week": [1,3,5], "day_of_month": 15, "end_date": "2024-12-31"}`
- `PUT /tasks/{task_id}/recurrence` - Update recurrence
- `DELETE /tasks/{task_id}/recurrence` - Remove recurrence
- `GET /tasks/{task_id}/recurrence/instances` - Get recurring instances

### Notifications and Reminders

- `GET /notifications` - Get user notifications
  - Query params: `?unread_only=true&type=task_assigned&limit=50`
- `PUT /notifications/{notification_id}/read` - Mark notification as read
- `PUT /notifications/read-all` - Mark all notifications as read
- `DELETE /notifications/{notification_id}` - Delete notification
- `GET /notifications/preferences` - Get notification preferences
- `PUT /notifications/preferences` - Update preferences
  - Body: `{"notification_type": "task_due", "channel": "email", "enabled": true, "frequency": "immediate"}`
- `POST /tasks/{task_id}/reminders` - Create task reminder
  - Body: `{"remind_at": "2024-01-20T10:00:00Z", "message": "string"}`
- `GET /tasks/{task_id}/reminders` - Get task reminders
- `DELETE /reminders/{reminder_id}` - Delete reminder

### Webhooks

- `GET /webhooks` - List webhook subscriptions
- `POST /webhooks` - Create webhook subscription
  - Body: `{"name": "string", "url": "https://example.com/hook", "events": ["task.created", "task.updated"], "secret": "string"}`
- `PUT /webhooks/{webhook_id}` - Update webhook
- `DELETE /webhooks/{webhook_id}` - Delete webhook
- `POST /webhooks/{webhook_id}/test` - Test webhook delivery
- `GET /webhooks/{webhook_id}/deliveries` - Get delivery history

### Calendar Integration

- `GET /calendar/integrations` - List calendar integrations
- `POST /calendar/integrations` - Add calendar integration
  - Body: `{"provider": "google|microsoft", "calendar_id": "string", "calendar_name": "string", "access_token": "string"}`
- `PUT /calendar/integrations/{integration_id}` - Update integration
- `DELETE /calendar/integrations/{integration_id}` - Remove integration
- `POST /calendar/sync` - Manually trigger calendar sync
- `GET /calendar/oauth/authorize` - Get OAuth URL for calendar
- `POST /calendar/oauth/callback` - Handle OAuth callback

### Health Check

- `GET /health` - Application health status

## Features

### Core Features

- **JWT Authentication**: Secure token-based authentication
- **Task Management**: Full CRUD operations for tasks
- **User Isolation**: Each user can only access their own tasks
- **Input Validation**: Comprehensive request validation with Pydantic
- **Error Handling**: Consistent error responses
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

### Enhanced Task Properties

- **Priority Levels**: LOW, MEDIUM, HIGH, URGENT
- **Date Management**: Start date, due date tracking
- **Time Tracking**: Estimated hours and actual hours logged
- **Task Ordering**: Manual position-based ordering
- **Task Status**: TODO, IN_PROGRESS, DONE with completion timestamps

### Organization Features

- **Categories**: Organize tasks into categories with colors
- **Tags**: Flexible tagging system for tasks
- **Subtasks**: Hierarchical task structures
- **Task Dependencies**: Define task relationships and dependencies

### Collaboration Features

- **Project Management**: Create projects with team members
- **Role-Based Access**: OWNER, ADMIN, MEMBER, VIEWER roles
- **Task Assignment**: Assign tasks to team members
- **Task Sharing**: Share individual tasks with specific permissions (VIEW, EDIT, COMMENT)
- **Project Context**: Tasks can belong to projects with team-based permissions
- **Comments System**: Add comments to tasks with threaded replies
- **@Mentions**: Mention users in comments with automatic notification tracking
- **File Attachments**: Upload and manage file attachments on tasks with size and type validation
- **Activity Tracking**: Complete audit trail of all task modifications with user attribution
  - Task creation, updates, and deletions
  - Status and priority changes
  - Assignment changes
  - Comments and mentions
  - File attachments
  - Time logging
  - All activities stored with timestamps and user information

### Advanced Search and Filtering

- **Full-text Search**: Search in task titles and descriptions
- **Advanced Filters**: Complex filtering with multiple operators (equals, contains, greater than, etc.)
- **Multi-criteria Search**: Filter by status, priority, dates, categories, tags, assigned user
- **Saved Searches**: Save and reuse complex search queries
- **Bulk Operations**: Update multiple tasks at once (status, priority, tags, etc.)
- **Search Suggestions**: Get intelligent filter suggestions based on your data
- **Project-based Views**: View all tasks within a project
- **Shared Tasks View**: See tasks shared with you
- **Pagination**: Built-in pagination for all list endpoints

### Analytics and Reporting

- **Time Tracking**: Log hours worked on tasks with detailed time logs
- **Task Statistics**: Get comprehensive statistics including completion rates and overdue tasks
- **Productivity Trends**: Track productivity over weeks, months, or quarters
- **Time Reports**: Generate detailed time tracking reports grouped by task, project, or day
- **Distribution Analysis**: Visualize task distribution by categories and tags
- **Team Performance**: Monitor team member performance metrics in projects
- **Export Functionality**: Export task data to CSV or Excel formats for external analysis
- **Date Range Filtering**: All analytics support custom date ranges
- **Project-specific Analytics**: Filter all metrics by specific projects

### Background Processing

- **Asynchronous Task Processing**: Celery-based background job processing
- **Scheduled Tasks**: Automatic processing of recurring tasks and reminders
- **Email Notifications**: Background email sending with retry logic
- **Webhook Delivery**: Reliable webhook delivery with exponential backoff
- **Analytics Computation**: Pre-compute analytics data for better performance
- **Notification Cleanup**: Automatic cleanup of old notifications

### Integrations

- **Calendar Sync**: Two-way sync with Google Calendar and Microsoft Outlook
- **Webhook System**: Real-time event notifications to external systems
- **Export/Import**: Data portability with CSV and Excel formats
- **OAuth2 Support**: Secure authentication for external calendar services

### Performance and Reliability

- **Redis Caching**: High-performance caching for frequently accessed data
- **Connection Pooling**: Efficient database connection management
- **Pagination**: All list endpoints support pagination
- **Bulk Operations**: Efficient bulk updates for multiple tasks
- **Transaction Management**: ACID compliance for data integrity
- **Error Recovery**: Automatic retry logic for failed operations

## Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User accounts and authentication
- **tasks**: Task records with all properties
- **projects**: Project management with team collaboration
- **project_members**: Project team membership and roles
- **categories**: Task categorization
- **tags**: Flexible tagging system
- **task_tags**: Many-to-many relationship for task tags
- **task_categories**: Many-to-many relationship for task categories
- **task_dependencies**: Task dependency relationships
- **task_shares**: Individual task sharing permissions
- **comments**: Task comments with threading support
- **comment_mentions**: User mentions in comments
- **file_attachments**: File uploads attached to tasks
- **notifications**: In-app notifications
- **notification_preferences**: User notification settings
- **task_reminders**: Scheduled task reminders
- **recurring_task_templates**: Templates for recurring tasks
- **webhook_subscriptions**: Webhook configuration
- **webhook_deliveries**: Webhook delivery history
- **calendar_integrations**: External calendar connections
- **task_calendar_syncs**: Task-calendar sync mappings
- **saved_searches**: User's saved search queries
- **time_logs**: Time tracking entries

## Git Workflow

### Commit Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for consistent commit messages. All commits are validated by commitlint.

#### Commit Format

```
<type>(<scope>): <subject>
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependency changes
- `ci`: CI/CD changes
- `chore`: Other changes

#### Scopes

- `root`: Root-level changes
- `backend`: Backend application
- `web`: Frontend application (future)
- `docker`: Docker-related changes
- `deps`: Dependencies

#### Examples

```bash
feat(backend): add task priority filtering
fix(backend): resolve JWT token expiration issue
docs(root): update API documentation
chore(deps): update fastapi to 0.115.0
```

### Git Hooks

The repository uses Git hooks to ensure code quality:

- **pre-commit**: Runs lint-staged to format and lint changed files
- **commit-msg**: Validates commit message format

To set a custom commit message template:

```bash
git config --local commit.template .gitmessage
```

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

### Webhook Events

The following events are available for webhook subscriptions:

- `task.created` - New task created
- `task.updated` - Task updated
- `task.deleted` - Task deleted
- `task.completed` - Task marked as done
- `task.assigned` - Task assigned to user
- `comment.created` - Comment added to task
- `comment.mention` - User mentioned in comment
- `project.member_added` - Member added to project
- `project.member_removed` - Member removed from project

### Development Tips

1. **Environment Setup**: Always use a virtual environment to avoid dependency conflicts
2. **Database Migrations**: Run `alembic upgrade head` after pulling changes
3. **Background Tasks**: Start Celery workers when testing features that use background processing
   - macOS users: Use `--pool=solo` to avoid fork safety issues
   - Set `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before starting workers
4. **Redis Required**: Many features require Redis, ensure it's running
5. **Test Data**: Use the factory classes in `tests/factories/` to generate test data
6. **API Testing**: Use the Swagger UI at `/docs` for interactive API testing
7. **Logging**: Check `app.log` for detailed application logs
8. **Performance**: Use Redis caching for frequently accessed data

### Troubleshooting Activity Tracking

If activities are not being logged:

1. **Check Celery Workers**: Ensure Celery workers are running

   ```bash
   ps aux | grep celery
   ```

2. **Check Redis**: Verify Redis is running and accessible

   ```bash
   redis-cli ping  # Should return PONG
   ```

3. **Check Database**: Verify the task_activities table exists

   ```bash
   cd apps/backend
   alembic current  # Should show the latest migration
   ```

4. **macOS Fork Issues**: If you see "fork safety" errors on macOS:

   ```bash
   export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
   celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo
   ```

5. **Debug Celery Tasks**: Check Celery logs for task execution
   ```bash
   celery -A app.core.celery_app:celery_app worker --loglevel=debug --pool=solo
   ```

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

## 📋 Quick Reference

### Essential Commands

```bash
# First time setup
./setup.sh

# Daily development
pnpm docker:up         # Start all services
pnpm dev:backend       # Start backend with hot reload
pnpm dev:web          # Start frontend dev server
pnpm dev              # Start both backend and frontend
pnpm test:backend      # Run tests
pnpm docker:logs       # View logs

# Stop everything
pnpm docker:down
```

### Service URLs

- Frontend App: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Celery UI: http://localhost:5555
- Health Check: http://localhost:8000/health

### Project Locations

- Backend Code: `apps/backend/`
- API Endpoints: `apps/backend/app/api/`
- Business Logic: `apps/backend/app/services/`
- Database Models: `apps/backend/app/db/models.py`
- Tests: `apps/backend/tests/`
- Frontend Code: `apps/web/`
- UI Components: `apps/web/components/`
- Pages: `apps/web/app/`

## License

This project is open source and available under the MIT License.
