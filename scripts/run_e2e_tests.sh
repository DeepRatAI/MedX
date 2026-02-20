#!/bin/bash
# =============================================================================
# MedeX E2E Tests Runner
# =============================================================================
# This script starts the necessary services and runs E2E tests with Playwright.
#
# Usage:
#   ./scripts/run_e2e_tests.sh [options]
#
# Options:
#   --api-only    Run only API tests (no UI tests)
#   --ui-only     Run only UI tests (requires Streamlit running)
#   --headed      Run browser tests in headed mode (visible browser)
#   --critical    Run only critical path tests
#   --no-start    Don't start services (use existing)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_API=true
RUN_UI=true
HEADED=""
CRITICAL=""
START_SERVICES=true
API_PID=""
STREAMLIT_PID=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --api-only)
            RUN_UI=false
            ;;
        --ui-only)
            RUN_API=false
            ;;
        --headed)
            HEADED="--headed"
            ;;
        --critical)
            CRITICAL="-m critical"
            ;;
        --no-start)
            START_SERVICES=false
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# Function to print status
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    
    if [ -n "$API_PID" ]; then
        print_status "Stopping API server (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ -n "$STREAMLIT_PID" ]; then
        print_status "Stopping Streamlit server (PID: $STREAMLIT_PID)"
        kill $STREAMLIT_PID 2>/dev/null || true
    fi
    
    print_success "Cleanup complete"
}

trap cleanup EXIT

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
else
    print_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Start services if requested
if [ "$START_SERVICES" = true ]; then
    
    # Start API server
    if [ "$RUN_API" = true ]; then
        print_status "Starting API server on port 8000..."
        python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
        API_PID=$!
        sleep 3
        
        # Check if API is running
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API server started successfully"
        else
            print_error "Failed to start API server"
            exit 1
        fi
    fi
    
    # Start Streamlit for UI tests
    if [ "$RUN_UI" = true ]; then
        print_status "Starting Streamlit server on port 8501..."
        streamlit run streamlit_app.py --server.port 8501 --server.headless true &
        STREAMLIT_PID=$!
        sleep 5
        
        # Check if Streamlit is running
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            print_success "Streamlit server started successfully"
        else
            print_warning "Streamlit may still be initializing..."
        fi
    fi
fi

# Run tests
print_status "Running E2E tests..."
echo ""
echo "============================================================"
echo "  MedeX E2E Test Suite"
echo "============================================================"
echo ""

# Build pytest command
PYTEST_CMD="python -m pytest tests/e2e/"

if [ "$RUN_API" = true ] && [ "$RUN_UI" = false ]; then
    PYTEST_CMD="$PYTEST_CMD/test_api_e2e.py"
elif [ "$RUN_UI" = true ] && [ "$RUN_API" = false ]; then
    PYTEST_CMD="$PYTEST_CMD/test_ui_e2e.py"
fi

PYTEST_CMD="$PYTEST_CMD $HEADED $CRITICAL -v"

print_status "Executing: $PYTEST_CMD"
echo ""

# Run pytest
$PYTEST_CMD

TEST_EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "All E2E tests passed!"
else
    print_error "Some E2E tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "============================================================"

exit $TEST_EXIT_CODE
