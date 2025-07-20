#!/bin/bash

# Celery Worker Startup Script for Task Management Application
# This script starts a Celery worker with appropriate configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
WORKER_NAME="worker1"
CONCURRENCY=4
LOGLEVEL="info"
QUEUES="default,notifications,recurring,webhooks,analytics,reminders"
PIDFILE=""
LOGFILE=""
DETACH=false

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --name NAME         Worker name (default: worker1)"
    echo "  -c, --concurrency NUM   Number of concurrent processes (default: 4)"
    echo "  -l, --loglevel LEVEL    Log level (default: info)"
    echo "  -q, --queues QUEUES     Comma-separated queue names (default: all queues)"
    echo "  -p, --pidfile FILE      PID file path"
    echo "  -f, --logfile FILE      Log file path"
    echo "  -d, --detach            Run as daemon"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 -n notifications_worker -q notifications"
    echo "  $0 -c 8 -l debug                     # High concurrency with debug logging"
    echo "  $0 -d -p /var/run/celery.pid         # Run as daemon"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            WORKER_NAME="$2"
            shift 2
            ;;
        -c|--concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        -l|--loglevel)
            LOGLEVEL="$2"
            shift 2
            ;;
        -q|--queues)
            QUEUES="$2"
            shift 2
            ;;
        -p|--pidfile)
            PIDFILE="$2"
            shift 2
            ;;
        -f|--logfile)
            LOGFILE="$2"
            shift 2
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected. Make sure you've activated the virtual environment.${NC}"
fi

# Check if Redis is running
echo -e "${BLUE}Checking Redis connection...${NC}"
if ! python -c "
import redis
from app.core.config import settings
try:
    r = redis.Redis.from_url(settings.redis_url)
    r.ping()
    print('✓ Redis connection successful')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${RED}Redis connection failed. Please ensure Redis is running.${NC}"
    exit 1
fi

# Check if database is accessible
echo -e "${BLUE}Checking database connection...${NC}"
if ! python -c "
from app.db.database import engine
try:
    with engine.connect() as conn:
        pass
    print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${RED}Database connection failed. Please check your database configuration.${NC}"
    exit 1
fi

# Build the celery command
CELERY_CMD="celery -A app.core.celery_app worker"
CELERY_CMD="$CELERY_CMD --hostname=${WORKER_NAME}@%h"
CELERY_CMD="$CELERY_CMD --concurrency=$CONCURRENCY"
CELERY_CMD="$CELERY_CMD --loglevel=$LOGLEVEL"
CELERY_CMD="$CELERY_CMD --queues=$QUEUES"

# Add optional parameters
if [[ -n "$PIDFILE" ]]; then
    CELERY_CMD="$CELERY_CMD --pidfile=$PIDFILE"
fi

if [[ -n "$LOGFILE" ]]; then
    CELERY_CMD="$CELERY_CMD --logfile=$LOGFILE"
fi

if [[ "$DETACH" == true ]]; then
    CELERY_CMD="$CELERY_CMD --detach"
fi

# Display configuration
echo -e "${GREEN}Starting Celery Worker with configuration:${NC}"
echo -e "  Worker Name: ${WORKER_NAME}"
echo -e "  Concurrency: ${CONCURRENCY}"
echo -e "  Log Level: ${LOGLEVEL}"
echo -e "  Queues: ${QUEUES}"
if [[ -n "$PIDFILE" ]]; then
    echo -e "  PID File: ${PIDFILE}"
fi
if [[ -n "$LOGFILE" ]]; then
    echo -e "  Log File: ${LOGFILE}"
fi
echo -e "  Detached: ${DETACH}"
echo ""

# Create directories for PID and log files if needed
if [[ -n "$PIDFILE" ]]; then
    mkdir -p "$(dirname "$PIDFILE")"
fi
if [[ -n "$LOGFILE" ]]; then
    mkdir -p "$(dirname "$LOGFILE")"
fi

echo -e "${BLUE}Executing: ${CELERY_CMD}${NC}"
echo ""

# Execute the command
exec $CELERY_CMD