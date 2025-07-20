# Contributing to Task Management Monorepo

## Table of Contents
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Guidelines](#commit-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Set up the development environment: `./setup.sh`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Workflow

### Prerequisites
- Node.js 18+
- pnpm 9+
- Python 3.11+
- Docker & Docker Compose

### Setup
```bash
# Install dependencies
pnpm install

# Start development services
pnpm docker:up

# Run development server
pnpm dev
```

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) to maintain a clean and consistent commit history.

### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without changing functionality
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system or dependency changes
- **ci**: CI/CD configuration changes
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverting a previous commit

### Scopes
- **root**: Root-level changes
- **backend**: Backend application changes
- **web**: Frontend application changes (future)
- **shared**: Shared packages/utilities
- **docker**: Docker-related changes
- **deps**: Dependency updates
- **release**: Release-related changes
- **ci**: CI/CD changes
- **docs**: Documentation changes

### Examples

```bash
# Feature
feat(backend): add user authentication endpoints

# Bug fix
fix(backend): resolve task deletion permission issue

# Documentation
docs(root): update API documentation

# Dependency update
chore(deps): update fastapi to 0.115.0

# Multiple scopes
refactor(backend,shared): extract common validation logic
```

### Commit Message Rules
1. Use present tense ("add feature" not "added feature")
2. Use lowercase for the subject line
3. Don't end the subject line with a period
4. Limit the subject line to 100 characters
5. Separate subject from body with a blank line
6. Use the body to explain what and why, not how

## Code Style

### Python (Backend)
- Follow PEP 8
- Use `ruff` for linting and formatting
- Type hints are required for all functions
- Maximum line length: 100 characters

```bash
# Format code
cd apps/backend && ruff format .

# Lint code
cd apps/backend && ruff check .

# Type check
cd apps/backend && mypy .
```

### TypeScript/JavaScript (Future)
- Use ESLint and Prettier
- Follow the project's ESLint configuration
- Use TypeScript for all new code

## Testing

### Backend Tests
```bash
# Run all backend tests
pnpm test:backend

# Run specific test file
cd apps/backend && pytest tests/test_file.py

# Run with coverage
cd apps/backend && pytest --cov=app tests/
```

### Writing Tests
- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

## Pull Request Process

1. **Before Creating a PR**
   - Ensure all tests pass: `pnpm test`
   - Run linting: `pnpm lint`
   - Run type checking: `pnpm type-check`
   - Update documentation if needed

2. **PR Title**
   - Follow the same convention as commit messages
   - Example: `feat(backend): add task priority system`

3. **PR Description**
   - Describe what changes were made and why
   - Link related issues
   - Include screenshots for UI changes
   - List any breaking changes

4. **PR Checklist**
   - [ ] Tests pass
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Commit messages follow convention

5. **Review Process**
   - Address reviewer feedback promptly
   - Keep discussions focused and professional
   - Request re-review after making changes

## Git Hooks

The repository uses Git hooks to ensure code quality:

- **pre-commit**: Runs lint-staged to format and lint changed files
- **commit-msg**: Validates commit message format with commitlint

If you need to bypass hooks in exceptional cases:
```bash
git commit --no-verify -m "your message"
```

## Questions?

If you have questions about contributing, please:
1. Check existing issues and PRs
2. Review the documentation
3. Open a discussion or issue

Thank you for contributing! 🎉