#!/bin/bash

# Celery Beat Scheduler Startup Script for Task Management Application
# This script starts the Celery Beat scheduler for periodic tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
LOGLEVEL="info"
PIDFILE=""
LOGFILE=""
SCHEDULE_FILE="celerybeat-schedule"
DETACH=false

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -l, --loglevel LEVEL    Log level (default: info)"
    echo "  -s, --schedule FILE     Schedule database file (default: celerybeat-schedule)"
    echo "  -p, --pidfile FILE      PID file path"
    echo "  -f, --logfile FILE      Log file path"
    echo "  -d, --detach            Run as daemon"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 -l debug                          # Debug logging"
    echo "  $0 -d -p /var/run/celerybeat.pid     # Run as daemon"
    echo "  $0 -s /tmp/beat-schedule              # Custom schedule file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--loglevel)
            LOGLEVEL="$2"
            shift 2
            ;;
        -s|--schedule)
            SCHEDULE_FILE="$2"
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

# Warn about existing schedule file
if [[ -f "$SCHEDULE_FILE" ]]; then
    echo -e "${YELLOW}Warning: Schedule file '$SCHEDULE_FILE' already exists.${NC}"
    echo -e "${YELLOW}Celery Beat will use the existing schedule. Delete it to use the latest configuration.${NC}"
fi

# Build the celery beat command
CELERY_CMD="celery -A app.core.celery_app beat"
CELERY_CMD="$CELERY_CMD --loglevel=$LOGLEVEL"
CELERY_CMD="$CELERY_CMD --schedule=$SCHEDULE_FILE"

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
echo -e "${GREEN}Starting Celery Beat Scheduler with configuration:${NC}"
echo -e "  Log Level: ${LOGLEVEL}"
echo -e "  Schedule File: ${SCHEDULE_FILE}"
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

# Display scheduled tasks
echo -e "${BLUE}Configured periodic tasks:${NC}"
python -c "
from app.core.celery_app import celery_app
for name, task in celery_app.conf.beat_schedule.items():
    print(f'  • {name}: {task[\"task\"]} (every {task[\"schedule\"]}s)')
"
echo ""

echo -e "${BLUE}Executing: ${CELERY_CMD}${NC}"
echo ""

# Execute the command
exec $CELERY_CMD