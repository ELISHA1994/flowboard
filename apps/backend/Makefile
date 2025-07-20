.PHONY: help install test test-unit test-integration test-e2e coverage lint format clean run migrate

help:
	@echo "Available commands:"
	@echo "  make install           - Install all dependencies"
	@echo "  make test             - Run all tests with coverage"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e         - Run end-to-end tests only"
	@echo "  make coverage         - Generate HTML coverage report"
	@echo "  make lint             - Run linting checks"
	@echo "  make format           - Format code with black and isort"
	@echo "  make clean            - Remove generated files"
	@echo "  make run              - Run the application"
	@echo "  make migrate          - Run database migrations"

install:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

test:
	pytest

test-unit:
	pytest -m unit --cov-fail-under=0

test-integration:
	pytest -m integration --cov-fail-under=0

test-e2e:
	pytest -m e2e --cov-fail-under=0

coverage:
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 app tests
	mypy app tests
	black --check app tests
	isort --check-only app tests

format:
	black app tests
	isort app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .mypy_cache

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head