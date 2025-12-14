#!/bin/bash

# ===========================================
# QF DAO Funding - Complete Setup Script
# ===========================================
# This script installs all dependencies and starts all services
# Run with: chmod +x setup.sh && ./setup.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Directories
SMART_CONTRACTS_DIR="$SCRIPT_DIR/smart-contracts"
BACKEND_DIR="$SCRIPT_DIR/backend"
DONCOIN_DIR="$BACKEND_DIR/doncoin"
FRONTEND_DIR="$SCRIPT_DIR/my-app"
VENV_DIR="$BACKEND_DIR/venv"

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_status() {
    echo -e "${YELLOW}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        print_success "Node.js $NODE_VERSION"
    else
        print_error "Node.js not found. Please install Node.js v18+"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm -v)
        print_success "npm v$NPM_VERSION"
    else
        print_error "npm not found. Please install npm"
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "$PYTHON_VERSION"
    else
        print_error "Python3 not found. Please install Python 3.10+"
        exit 1
    fi
}

# Install Smart Contract dependencies
setup_smart_contracts() {
    print_header "Setting up Smart Contracts"
    
    cd "$SMART_CONTRACTS_DIR"
    
    if [ -d "node_modules" ]; then
        print_status "node_modules exists, skipping npm install"
    else
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    print_success "Smart contracts ready"
}

# Setup Python virtual environment and install dependencies
setup_backend() {
    print_header "Setting up Backend"
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install requirements
    print_status "Installing Python dependencies..."
    cd "$DONCOIN_DIR"
    pip install -r requirements.txt --quiet
    
    # Run migrations
    print_status "Running database migrations..."
    python manage.py migrate --no-input
    
    print_success "Backend ready"
}

# Install Frontend dependencies
setup_frontend() {
    print_header "Setting up Frontend"
    
    cd "$FRONTEND_DIR"
    
    if [ -d "node_modules" ]; then
        print_status "node_modules exists, skipping npm install"
    else
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    print_success "Frontend ready"
}

# Create .env file if not exists
setup_env() {
    print_header "Setting up Environment"
    
    ENV_FILE="$SCRIPT_DIR/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        print_status "Creating .env file..."
        cat > "$ENV_FILE" << 'EOF'
# Host Configuration
HOST_IP=127.0.0.1

# Ports
HARDHAT_PORT=8545
DJANGO_PORT=8000
NEXT_PORT=3000

# URLs
HARDHAT_RPC_URL=http://127.0.0.1:8545
DJANGO_API_URL=http://127.0.0.1:8000

# Database - SQLite (default for development)
# For PostgreSQL, uncomment and configure:
# DB_NAME=doncoin
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
EOF
        print_success ".env file created"
    else
        print_status ".env file already exists"
    fi
}

# Start all services
start_services() {
    print_header "Starting All Services"
    
    # Create logs directory
    LOGS_DIR="$SCRIPT_DIR/logs"
    mkdir -p "$LOGS_DIR"
    
    # Start Hardhat Node
    print_status "Starting Hardhat Node..."
    cd "$SMART_CONTRACTS_DIR"
    npx hardhat node > "$LOGS_DIR/hardhat.log" 2>&1 &
    HARDHAT_PID=$!
    echo $HARDHAT_PID > "$LOGS_DIR/hardhat.pid"
    sleep 5
    print_success "Hardhat Node running (PID: $HARDHAT_PID)"
    
    # Deploy contracts
    print_status "Deploying Smart Contracts..."
    npx hardhat run scripts/deploy.js --network localhost >> "$LOGS_DIR/hardhat.log" 2>&1
    print_success "Contracts deployed"
    
    # Activate venv for backend services
    source "$VENV_DIR/bin/activate"
    
    # Start Django Backend
    print_status "Starting Django Backend..."
    cd "$DONCOIN_DIR"
    python manage.py runserver 0.0.0.0:8000 > "$LOGS_DIR/django.log" 2>&1 &
    DJANGO_PID=$!
    echo $DJANGO_PID > "$LOGS_DIR/django.pid"
    print_success "Django running (PID: $DJANGO_PID)"
    
    # Start Indexer
    print_status "Starting Blockchain Indexer..."
    python manage.py run_indexer > "$LOGS_DIR/indexer.log" 2>&1 &
    INDEXER_PID=$!
    echo $INDEXER_PID > "$LOGS_DIR/indexer.pid"
    print_success "Indexer running (PID: $INDEXER_PID)"
    
    # Start Frontend
    print_status "Starting Next.js Frontend..."
    cd "$FRONTEND_DIR"
    npm run dev > "$LOGS_DIR/nextjs.log" 2>&1 &
    NEXT_PID=$!
    echo $NEXT_PID > "$LOGS_DIR/nextjs.pid"
    print_success "Frontend running (PID: $NEXT_PID)"
    
    # Wait for services to start
    sleep 3
    
    print_header "🎉 All Services Started!"
    echo ""
    echo -e "  ${GREEN}Frontend:${NC}   http://localhost:3000"
    echo -e "  ${GREEN}Backend:${NC}    http://localhost:8000"
    echo -e "  ${GREEN}Blockchain:${NC} http://localhost:8545"
    echo ""
    echo -e "  ${YELLOW}Logs:${NC} $LOGS_DIR/"
    echo ""
    echo -e "  ${YELLOW}To stop all services:${NC} ./stop.sh"
    echo ""
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    if [ -f "$LOGS_DIR/hardhat.pid" ]; then kill $(cat "$LOGS_DIR/hardhat.pid") 2>/dev/null; fi
    if [ -f "$LOGS_DIR/django.pid" ]; then kill $(cat "$LOGS_DIR/django.pid") 2>/dev/null; fi
    if [ -f "$LOGS_DIR/indexer.pid" ]; then kill $(cat "$LOGS_DIR/indexer.pid") 2>/dev/null; fi
    if [ -f "$LOGS_DIR/nextjs.pid" ]; then kill $(cat "$LOGS_DIR/nextjs.pid") 2>/dev/null; fi
    exit
}

trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     QF DAO Funding - Setup Script         ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    
    check_prerequisites
    setup_env
    setup_smart_contracts
    setup_backend
    setup_frontend
    start_services
    
    # Keep script running to maintain background processes
    echo "Press Ctrl+C to stop all services..."
    wait
}

main "$@"
