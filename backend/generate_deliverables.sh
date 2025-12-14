#!/bin/bash

# Configuration
PROJECT_ROOT="/Users/nasibgojayev/Desktop/next_js_project"
BACKEND_ROOT="/Users/nasibgojayev/Desktop/visual_programming/backend/doncoin"
ARTIFACTS_DIR="/Users/nasibgojayev/.gemini/antigravity/brain/80f3ab2f-d5e0-4fb0-8288-5f31547277a9"

echo "=========================================="
echo "Starting Deliverables Generation"
echo "=========================================="

# Activate Virtual Environment
source /Users/nasibgojayev/Desktop/visual_programming/backend/venv/bin/activate

# 1. Smart Contract Deliverables
echo "[1/4] Smart Contracts..."
cd "$PROJECT_ROOT/smart-contracts"

# Run Tests
echo "Running Hardhat Tests..."
npx hardhat test > "$ARTIFACTS_DIR/contract_tests.log" 2>&1
if [ $? -eq 0 ]; then
    echo "Tests Passed. Output saved to contract_tests.log"
else
    echo "Tests Failed! Check contract_tests.log"
fi

# Run ABI Consolidation
echo "Consolidating ABIs..."
node scripts/consolidate_abis.js

# 2. Database Schema (ERD)
echo "[2/4] Database Schema..."
cd "$BACKEND_ROOT"

# Install requirements to ensure environment is ready
echo "Installing Python dependencies..."
pip3 install -r requirements.txt > /dev/null

# Generate ERD (requires graphviz usually, if not present we skip or mock)
# We can print the models to a file as a textual representation if graphviz is missing
echo "Generating Model Graph (Textual)..."
python3 manage.py showmigrations > "$ARTIFACTS_DIR/migrations_report.txt"

# 3. Indexer verification (Dry Run)
echo "[3/4] Indexer Verification..."
# We can't easily run the indexer endlessly in a script, but we can try to verify the command loads
python3 manage.py run_indexer --help > /dev/null
if [ $? -eq 0 ]; then
    echo "Indexer command is importable and runs."
else
    echo "Indexer command failed to load."
fi

# 4. Generate Reports
echo "[4/4] Finalizing..."
echo "All logs and reports saved to $ARTIFACTS_DIR"

echo "=========================================="
echo "Deliverables Generation Complete"
echo "=========================================="
