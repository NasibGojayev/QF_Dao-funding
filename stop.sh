#!/bin/bash

# ===========================================
# QF DAO Funding - Stop All Services Script
# ===========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}Stopping all services...${NC}"
echo ""

# Stop by PID files
stop_service() {
    local name=$1
    local pid_file="$LOGS_DIR/$2.pid"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "${GREEN}✓${NC} Stopped $name (PID: $PID)"
        else
            echo "  $name not running"
        fi
        rm -f "$pid_file"
    else
        echo "  $name PID file not found"
    fi
}

stop_service "Hardhat Node" "hardhat"
stop_service "Django Backend" "django"
stop_service "Indexer" "indexer"
stop_service "Next.js Frontend" "nextjs"

# Also kill any remaining processes on common ports
echo ""
echo -e "${YELLOW}Cleaning up ports...${NC}"

for PORT in 3000 8000 8545; do
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Freed port $PORT"
    fi
done

echo ""
echo -e "${GREEN}All services stopped!${NC}"
echo ""
