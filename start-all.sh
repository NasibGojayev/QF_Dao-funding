#!/bin/bash

# Configuration
# ==========================================
# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Workspace Paths (Adjust relative to this script location)
# Assumes script is in visual_programming/backend
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/.env"
BACKEND_DIR="$SCRIPT_DIR/backend/doncoin"
SMART_CONTRACTS_DIR="$SCRIPT_DIR/smart-contracts"
FRONTEND_DIR="$SCRIPT_DIR/my-app"

# Helper Functions
# ==========================================
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found at $ENV_FILE"
        print_error "Please create one using .env.example"
        exit 1
    fi
    print_success "Found .env file"
    
    # Load environment variables
    set -a
    source "$ENV_FILE"
    set +a
}

# Cleanup function to kill background processes
cleanup() {
    print_status "Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup SIGINT

# Main Script
# ==========================================
echo "=========================================="
echo "   DonCoin Stack Startup Script"
echo "=========================================="

check_env

print_status "Starting Stack on IP: ${GREEN}$HOST_IP${NC}"

# Create centralized logs directory
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR/backend" "$LOGS_DIR/indexer" "$LOGS_DIR/hardhat" "$LOGS_DIR/frontend"
print_success "Created logs directory structure at $LOGS_DIR"

# 1. Start Hardhat Node (with verbose logging)
print_status "Starting Hardhat Node..."
cd "$SMART_CONTRACTS_DIR" || exit
npx hardhat node --hostname 0.0.0.0 > "$LOGS_DIR/hardhat/hardhat.log" 2>&1 &
HARDHAT_PID=$!
print_success "Hardhat running (PID: $HARDHAT_PID). Logs: logs/hardhat/hardhat.log"

# Wait for Hardhat to spin up
sleep 5

# 2. Start Django Backend
print_status "Starting Django Backend..."
cd "$BACKEND_DIR" || exit
# Activate virtual environment if it exists in parent directory
if [ -f "../venv/bin/activate" ]; then
    source "../venv/bin/activate"
elif [ -f "venv/bin/activate" ]; then
    source "venv/bin/activate"
fi

python manage.py runserver 0.0.0.0:$DJANGO_PORT > "$LOGS_DIR/backend/server.log" 2>&1 &
DJANGO_PID=$!
print_success "Django running (PID: $DJANGO_PID). Logs: backend/django.log"

# 3. Start Indexer
print_status "Starting Blockchain Indexer..."
python manage.py run_indexer > "$LOGS_DIR/indexer/indexer.log" 2>&1 &
INDEXER_PID=$!
print_success "Indexer running (PID: $INDEXER_PID). Logs: logs/indexer/indexer.log"

# 4. Start Next.js Frontend
print_status "Starting Next.js Frontend..."
cd "$FRONTEND_DIR" || exit
# Export env vars explicitly for Next.js
export NEXT_PUBLIC_HARDHAT_RPC=$HARDHAT_RPC_URL
export NEXT_PUBLIC_API_URL=$DJANGO_API_URL

npm run dev -- -H $HOST_IP > "$LOGS_DIR/frontend/nextjs.log" 2>&1 &
NEXT_PID=$!
print_success "Next.js running (PID: $NEXT_PID). Logs: logs/frontend/nextjs.log"

echo ""
echo "=========================================="
echo "   All Services Started Successfully!"
echo "=========================================="
echo -e "Frontend:   ${GREEN}http://$HOST_IP:$NEXT_PORT${NC}"
echo -e "Backend:    ${GREEN}http://$HOST_IP:$DJANGO_PORT${NC}"
echo -e "Blockchain: ${GREEN}http://$HOST_IP:$HARDHAT_PORT${NC}"
echo ""
echo "Press Ctrl+C to stop all services."
echo "=========================================="

# Keep script running
wait
