#!/bin/bash

# Celery Monitoring Script for Task Management Application
# This script provides monitoring and management commands for Celery workers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
COMMAND="status"
REFRESH_INTERVAL=5
TIMEOUT=30

# Help function
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status      Show worker status (default)"
    echo "  inspect     Inspect workers and queues"
    echo "  stats       Show detailed statistics"
    echo "  active      Show active tasks"
    echo "  scheduled   Show scheduled tasks"
    echo "  reserved    Show reserved tasks"
    echo "  control     Control workers (ping, shutdown, etc.)"
    echo "  purge       Purge all tasks from queues"
    echo "  watch       Continuously monitor (refresh every 5s)"
    echo ""
    echo "Options:"
    echo "  -r, --refresh NUM   Refresh interval for watch mode (default: 5)"
    echo "  -t, --timeout NUM   Command timeout in seconds (default: 30)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Show status"
    echo "  $0 stats                # Show statistics"
    echo "  $0 watch                # Continuous monitoring"
    echo "  $0 control ping         # Ping all workers"
    echo "  $0 purge                # Purge all queues"
}

# Parse command line arguments
if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
    COMMAND="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--refresh)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # Pass remaining arguments to the command
            break
            ;;
    esac
done

# Header
print_header() {
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${CYAN}         Celery Monitor - Task Manager          ${NC}"
    echo -e "${CYAN}=================================================${NC}"
    echo ""
}

# Check if Redis is running
check_redis() {
    echo -e "${BLUE}Checking Redis connection...${NC}"
    if python -c "
import redis
from app.core.config import settings
try:
    r = redis.Redis.from_url(settings.redis_url)
    r.ping()
    print('✓ Redis is running')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo ""
else
    echo -e "${RED}Redis connection failed. Please ensure Redis is running.${NC}"
    exit 1
fi
}

# Show worker status
show_status() {
    echo -e "${GREEN}=== Worker Status ===${NC}"
    celery -A app.core.celery_app inspect stats --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}No workers found or workers not responding${NC}"
        return 1
    }
    echo ""
}

# Show detailed inspection
show_inspect() {
    echo -e "${GREEN}=== Worker Inspection ===${NC}"
    
    echo -e "${BLUE}Active Workers:${NC}"
    celery -A app.core.celery_app inspect active --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}No active workers found${NC}"
    }
    echo ""
    
    echo -e "${BLUE}Registered Tasks:${NC}"
    celery -A app.core.celery_app inspect registered --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}Could not get registered tasks${NC}"
    }
    echo ""
    
    echo -e "${BLUE}Queue Lengths:${NC}"
    python -c "
import redis
from app.core.config import settings
try:
    r = redis.Redis.from_url(settings.redis_url)
    queues = ['default', 'notifications', 'recurring', 'webhooks', 'analytics', 'reminders']
    for queue in queues:
        length = r.llen(queue)
        print(f'  {queue}: {length} tasks')
except Exception as e:
    print(f'Error checking queue lengths: {e}')
"
    echo ""
}

# Show statistics
show_stats() {
    echo -e "${GREEN}=== Detailed Statistics ===${NC}"
    celery -A app.core.celery_app inspect stats --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}Could not get worker statistics${NC}"
        return 1
    }
    echo ""
}

# Show active tasks
show_active() {
    echo -e "${GREEN}=== Active Tasks ===${NC}"
    celery -A app.core.celery_app inspect active --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}No active tasks found${NC}"
    }
    echo ""
}

# Show scheduled tasks
show_scheduled() {
    echo -e "${GREEN}=== Scheduled Tasks ===${NC}"
    celery -A app.core.celery_app inspect scheduled --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}No scheduled tasks found${NC}"
    }
    echo ""
}

# Show reserved tasks
show_reserved() {
    echo -e "${GREEN}=== Reserved Tasks ===${NC}"
    celery -A app.core.celery_app inspect reserved --timeout=$TIMEOUT 2>/dev/null || {
        echo -e "${YELLOW}No reserved tasks found${NC}"
    }
    echo ""
}

# Control workers
control_workers() {
    local action="$1"
    
    case "$action" in
        ping)
            echo -e "${GREEN}=== Pinging Workers ===${NC}"
            celery -A app.core.celery_app inspect ping --timeout=$TIMEOUT
            ;;
        shutdown)
            echo -e "${RED}=== Shutting Down Workers ===${NC}"
            echo -e "${YELLOW}Warning: This will shut down all workers!${NC}"
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                celery -A app.core.celery_app control shutdown --timeout=$TIMEOUT
            else
                echo "Cancelled."
            fi
            ;;
        revoke)
            echo -e "${YELLOW}=== Revoking Tasks ===${NC}"
            if [[ -n "$2" ]]; then
                celery -A app.core.celery_app control revoke "$2" --timeout=$TIMEOUT
            else
                echo "Usage: $0 control revoke <task_id>"
            fi
            ;;
        *)
            echo "Available control commands: ping, shutdown, revoke"
            ;;
    esac
    echo ""
}

# Purge queues
purge_queues() {
    echo -e "${RED}=== Purging All Queues ===${NC}"
    echo -e "${YELLOW}Warning: This will delete all pending tasks!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        celery -A app.core.celery_app purge --force
    else
        echo "Cancelled."
    fi
    echo ""
}

# Watch mode - continuous monitoring
watch_mode() {
    echo -e "${GREEN}=== Continuous Monitoring (refresh every ${REFRESH_INTERVAL}s) ===${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo ""
    
    while true; do
        clear
        print_header
        echo -e "${CYAN}Last updated: $(date)${NC}"
        echo ""
        
        show_status
        show_inspect
        
        echo -e "${BLUE}Sleeping for ${REFRESH_INTERVAL} seconds...${NC}"
        sleep $REFRESH_INTERVAL
    done
}

# Main execution
print_header
check_redis

case "$COMMAND" in
    status)
        show_status
        ;;
    inspect)
        show_inspect
        ;;
    stats)
        show_stats
        ;;
    active)
        show_active
        ;;
    scheduled)
        show_scheduled
        ;;
    reserved)
        show_reserved
        ;;
    control)
        control_workers "$@"
        ;;
    purge)
        purge_queues
        ;;
    watch)
        watch_mode
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac