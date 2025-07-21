#!/bin/bash

# Comprehensive Celery Startup Script for Task Management Application
# This script starts workers, beat scheduler, and optional monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$PROJECT_ROOT/run"
LOG_DIR="$PROJECT_ROOT/logs"

# Default values
WORKERS=2
CONCURRENCY=4
LOGLEVEL="info"
DETACH=true
START_BEAT=true
START_MONITOR=false
ENVIRONMENT="development"

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "This script starts the complete Celery infrastructure for the task management application."
    echo ""
    echo "Options:"
    echo "  -w, --workers NUM       Number of worker processes (default: 2)"
    echo "  -c, --concurrency NUM   Concurrency per worker (default: 4)"
    echo "  -l, --loglevel LEVEL    Log level (default: info)"
    echo "  -e, --env ENV           Environment (default: development)"
    echo "  --no-beat              Don't start beat scheduler"
    echo "  --no-detach            Don't run as daemon"
    echo "  --monitor              Start monitoring in background"
    echo "  --stop                 Stop all running processes"
    echo "  --restart              Restart all processes"
    echo "  --status               Show status of running processes"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                            # Start with defaults"
    echo "  $0 -w 4 -c 8                  # 4 workers with 8 concurrency each"
    echo "  $0 --no-beat --monitor        # Workers only with monitoring"
    echo "  $0 --stop                     # Stop all processes"
    echo "  $0 --status                   # Show status"
}

# Stop all processes function (moved before argument parsing)
stop_all_processes() {
    echo -e "${YELLOW}Stopping all Celery processes...${NC}"
    
    # Stop workers
    for i in $(seq 1 10); do  # Check up to 10 workers
        local pidfile="$PID_DIR/worker${i}.pid"
        if [[ -f "$pidfile" ]]; then
            local pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  Stopping worker${i} (PID: $pid)"
                kill -TERM "$pid"
                # Wait for graceful shutdown
                local count=0
                while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                    sleep 1
                    ((count++))
                done
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "    Force killing worker${i}"
                    kill -KILL "$pid"
                fi
            fi
            rm -f "$pidfile"
        fi
    done
    
    # Stop beat
    local beat_pidfile="$PID_DIR/beat.pid"
    if [[ -f "$beat_pidfile" ]]; then
        local pid=$(cat "$beat_pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  Stopping beat scheduler (PID: $pid)"
            kill -TERM "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid"
            fi
        fi
        rm -f "$beat_pidfile"
    fi
    
    # Stop monitor
    local monitor_pidfile="$PID_DIR/monitor.pid"
    if [[ -f "$monitor_pidfile" ]]; then
        local pid=$(cat "$monitor_pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  Stopping monitor (PID: $pid)"
            kill -TERM "$pid"
        fi
        rm -f "$monitor_pidfile"
    fi
    
    echo -e "${GREEN}All processes stopped${NC}"
}

# Show status function (moved before argument parsing)
show_status() {
    echo -e "${CYAN}=== Celery Process Status ===${NC}"
    
    local running_count=0
    
    # Check workers
    echo -e "${BLUE}Workers:${NC}"
    for i in $(seq 1 10); do  # Check up to 10 workers
        local pidfile="$PID_DIR/worker${i}.pid"
        if [[ -f "$pidfile" ]]; then
            local pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ✓ worker${i} (PID: $pid)"
                ((running_count++))
            else
                echo -e "  ✗ worker${i} (stale PID file)"
                rm -f "$pidfile"
            fi
        fi
    done
    
    # Check beat
    echo -e "${BLUE}Beat Scheduler:${NC}"
    local beat_pidfile="$PID_DIR/beat.pid"
    if [[ -f "$beat_pidfile" ]]; then
        local pid=$(cat "$beat_pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  ✓ beat (PID: $pid)"
            ((running_count++))
        else
            echo -e "  ✗ beat (stale PID file)"
            rm -f "$beat_pidfile"
        fi
    else
        echo -e "  ✗ beat (not running)"
    fi
    
    # Check monitor
    echo -e "${BLUE}Monitor:${NC}"
    local monitor_pidfile="$PID_DIR/monitor.pid"
    if [[ -f "$monitor_pidfile" ]]; then
        local pid=$(cat "$monitor_pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  ✓ monitor (PID: $pid)"
            ((running_count++))
        else
            echo -e "  ✗ monitor (stale PID file)"
            rm -f "$monitor_pidfile"
        fi
    else
        echo -e "  ✗ monitor (not running)"
    fi
    
    echo ""
    echo -e "${GREEN}Total running processes: $running_count${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--workers)
            WORKERS="$2"
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
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --no-beat)
            START_BEAT=false
            shift
            ;;
        --no-detach)
            DETACH=false
            shift
            ;;
        --monitor)
            START_MONITOR=true
            shift
            ;;
        --stop)
            stop_all_processes
            exit 0
            ;;
        --restart)
            stop_all_processes
            sleep 2
            # Continue with startup
            shift
            ;;
        --status)
            show_status
            exit 0
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

# Create directories
create_directories() {
    mkdir -p "$PID_DIR" "$LOG_DIR"
    echo -e "${GREEN}Created directories:${NC}"
    echo -e "  PID files: $PID_DIR"
    echo -e "  Log files: $LOG_DIR"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check virtual environment
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    else
        echo -e "  ✓ Virtual environment: $VIRTUAL_ENV"
    fi
    
    # Check Redis
    if python -c "
import redis
from app.core.config import settings
try:
    r = redis.Redis.from_url(settings.redis_url)
    r.ping()
    print('  ✓ Redis connection successful')
except Exception as e:
    print(f'  ✗ Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        :
    else
        echo -e "${RED}Redis check failed. Exiting.${NC}"
        exit 1
    fi
    
    # Check database
    if python -c "
from app.db.database import engine
try:
    with engine.connect() as conn:
        pass
    print('  ✓ Database connection successful')
except Exception as e:
    print(f'  ✗ Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        :
    else
        echo -e "${RED}Database check failed. Exiting.${NC}"
        exit 1
    fi
    
    echo ""
}

# Functions defined above in the script

# Start workers
start_workers() {
    echo -e "${GREEN}Starting $WORKERS worker(s) with concurrency $CONCURRENCY...${NC}"
    
    for i in $(seq 1 $WORKERS); do
        local worker_name="worker${i}"
        local pidfile="$PID_DIR/${worker_name}.pid"
        local logfile="$LOG_DIR/${worker_name}.log"
        
        # Define queues for this worker
        local queues="default,notifications,recurring,webhooks,analytics,reminders"
        if [[ $i -eq 1 ]]; then
            # First worker handles all queues
            queues="default,notifications,recurring,webhooks,analytics,reminders"
        elif [[ $i -eq 2 ]]; then
            # Second worker focuses on notifications and reminders
            queues="notifications,reminders,default"
        else
            # Additional workers handle default and specific queues
            queues="default,analytics,webhooks"
        fi
        
        echo -e "  Starting $worker_name (queues: $queues)"
        
        if [[ "$DETACH" == true ]]; then
            "$SCRIPT_DIR/start_worker.sh" \
                --name "$worker_name" \
                --concurrency "$CONCURRENCY" \
                --loglevel "$LOGLEVEL" \
                --queues "$queues" \
                --pidfile "$pidfile" \
                --logfile "$logfile" \
                --detach &
        else
            "$SCRIPT_DIR/start_worker.sh" \
                --name "$worker_name" \
                --concurrency "$CONCURRENCY" \
                --loglevel "$LOGLEVEL" \
                --queues "$queues" &
        fi
        
        # Give worker time to start
        sleep 2
    done
    
    echo ""
}

# Start beat scheduler
start_beat() {
    if [[ "$START_BEAT" == true ]]; then
        echo -e "${GREEN}Starting beat scheduler...${NC}"
        
        local pidfile="$PID_DIR/beat.pid"
        local logfile="$LOG_DIR/beat.log"
        
        if [[ "$DETACH" == true ]]; then
            "$SCRIPT_DIR/start_beat.sh" \
                --loglevel "$LOGLEVEL" \
                --pidfile "$pidfile" \
                --logfile "$logfile" \
                --detach &
        else
            "$SCRIPT_DIR/start_beat.sh" \
                --loglevel "$LOGLEVEL" &
        fi
        
        # Give beat more time to start and write PID file
        sleep 4
        echo ""
    fi
}

# Start monitoring
start_monitoring() {
    if [[ "$START_MONITOR" == true ]]; then
        echo -e "${GREEN}Starting monitoring...${NC}"
        
        local pidfile="$PID_DIR/monitor.pid"
        local logfile="$LOG_DIR/monitor.log"
        
        nohup "$SCRIPT_DIR/monitor.sh" watch > "$logfile" 2>&1 &
        echo $! > "$pidfile"
        
        echo -e "  Monitor started (PID: $(cat $pidfile))"
        echo -e "  Log file: $logfile"
        echo ""
    fi
}

# Main execution
main() {
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${CYAN}    Starting Celery Infrastructure               ${NC}"
    echo -e "${CYAN}=================================================${NC}"
    echo ""
    
    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  Workers: $WORKERS"
    echo -e "  Concurrency per worker: $CONCURRENCY"
    echo -e "  Log level: $LOGLEVEL"
    echo -e "  Environment: $ENVIRONMENT"
    echo -e "  Start beat: $START_BEAT"
    echo -e "  Detached: $DETACH"
    echo -e "  Start monitor: $START_MONITOR"
    echo ""
    
    create_directories
    check_prerequisites
    
    # Stop any existing processes
    stop_all_processes
    
    start_workers
    start_beat
    start_monitoring
    
    echo -e "${GREEN}=================================================${NC}"
    echo -e "${GREEN}    Celery Infrastructure Started Successfully   ${NC}"
    echo -e "${GREEN}=================================================${NC}"
    echo ""
    
    if [[ "$DETACH" == true ]]; then
        show_status
        echo ""
        echo -e "${BLUE}All processes are running in the background.${NC}"
        echo -e "${BLUE}Use '$0 --status' to check status.${NC}"
        echo -e "${BLUE}Use '$0 --stop' to stop all processes.${NC}"
        echo -e "${BLUE}Use '$SCRIPT_DIR/monitor.sh' for detailed monitoring.${NC}"
    else
        echo -e "${YELLOW}Running in foreground mode. Press Ctrl+C to stop all processes.${NC}"
        
        # Set up signal handling
        trap 'echo ""; echo "Stopping all processes..."; stop_all_processes; exit 0' INT TERM
        
        # Wait for all background processes
        wait
    fi
}

# Execute main function
main