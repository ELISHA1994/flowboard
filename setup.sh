#!/bin/bash

# Task Management Monorepo Setup Script

echo "🚀 Setting up Task Management Monorepo..."

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

# Install dependencies
echo "📥 Installing dependencies..."
pnpm install

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "⚠️  Docker is not running. Please start Docker Desktop."
    echo "   After starting Docker, run: pnpm docker:up"
else
    echo "🐳 Starting Docker services..."
    docker-compose up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Run migrations
    echo "🗄️  Running database migrations..."
    docker-compose exec -T backend alembic upgrade head
    
    echo "✅ Setup complete!"
    echo ""
    echo "Services running:"
    echo "  - API: http://localhost:8000/docs"
    echo "  - Flower (Celery UI): http://localhost:5555"
    echo ""
    echo "To start development:"
    echo "  - All services: pnpm dev"
    echo "  - Backend only: pnpm dev:backend"
    echo "  - View logs: pnpm docker:logs"
fi