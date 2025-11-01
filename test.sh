#!/bin/bash

# Test runner for Enterprise Code Archaeologist
# This script runs tests for all components or a specific component

echo "🧪 Enterprise Code Archaeologist Test Runner"

# Function to print usage
usage() {
    echo "Usage: $0 [component]"
    echo "Components:"
    echo "  frontend - Run frontend tests only"
    echo "  api      - Run API tests only"
    echo "  scanner  - Run Scanner tests only"
    echo "  (no args) - Run all tests"
    echo ""
    echo "Requirements: uv (Python package manager) must be installed"
    echo "Install with: pip install uv"
    echo ""
    echo "Examples:"
    echo "  $0          # Run all tests"
    echo "  $0 api      # Run API tests only"
    echo "  $0 frontend # Run frontend tests only"
}

# Parse arguments
COMPONENT=${1:-"all"}

if [[ "$COMPONENT" == "help" || "$COMPONENT" == "--help" || "$COMPONENT" == "-h" ]]; then
    usage
    exit 0
fi

# Validate component argument
if [[ "$COMPONENT" != "all" && "$COMPONENT" != "frontend" && "$COMPONENT" != "api" && "$COMPONENT" != "scanner" ]]; then
    echo "❌ Invalid component: $COMPONENT"
    echo ""
    usage
    exit 1
fi

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if required commands are available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:"
    echo "   pip install uv"
    echo "   or visit: https://github.com/astral-sh/uv"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js and npm first."
    exit 1
fi

# Load development environment variables
if [ -f .env.dev ]; then
    export $(cat .env.dev | grep -v '^#' | xargs)
    echo "✅ Loaded .env.dev"
else
    echo "❌ Error: .env.dev file not found!"
    exit 1
fi

# Function to run API tests
run_api_tests() {
    echo ""
    echo "🔌 Running API Tests..."
    echo "======================"
    
    # Create virtual environment if needed
    if [ ! -d "api/.venv" ]; then
        echo "🐍 Creating API virtual environment..."
        cd api && uv venv && cd ..
    fi
    
    # Install dependencies
    cd api
    uv pip sync pyproject.toml
    
    # Run tests with app directory in Python path and suppress warnings
    PYTHONPATH=. uv run python -m pytest tests/ -v --tb=short -W ignore::UserWarning -W ignore::DeprecationWarning
    TEST_EXIT_CODE=$?
    cd ..
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ API tests passed"
    else
        echo "❌ API tests failed"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run Scanner tests
run_scanner_tests() {
    echo ""
    echo "🔍 Running Scanner Tests..."
    echo "=========================="
    
    # Create virtual environment if needed
    if [ ! -d "scanner/.venv" ]; then
        echo "🐍 Creating Scanner virtual environment..."
        cd scanner && uv venv && cd ..
    fi
    
    # Install dependencies
    cd scanner
    uv pip sync pyproject.toml
    
    # Run tests with current directory in Python path
    uv run python -m pytest -v --tb=short
    TEST_EXIT_CODE=$?
    cd ..
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ Scanner tests passed"
    else
        echo "❌ Scanner tests failed"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run Frontend tests
run_frontend_tests() {
    echo ""
    echo "⚛️ Running Frontend Tests..."
    echo "=========================="
    
    # Check if node_modules exists
    if [ ! -d "ui/node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        cd ui && npm install
        cd ..
    fi
    
    # Run tests
    cd ui
    npm test -- --watchAll=false --passWithNoTests
    TEST_EXIT_CODE=$?
    cd ..
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ Frontend tests passed"
    else
        echo "❌ Frontend tests failed"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run containerized tests
run_containerized_tests() {
    echo ""
    echo "🐳 Running Containerized Tests (if available)..."
    echo "================================================"
    
    # Check if containers are running
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            echo "🔌 Running API tests in container..."
            docker-compose exec -T app sh -c "cd /app && uv run python -m pytest tests/ -v --tb=short" || echo "⚠️ Container tests not available"
            
            echo "🔍 Running Scanner tests in container..."
            docker-compose exec -T scanner sh -c "cd /app && uv run python -m pytest -v --tb=short" || echo "⚠️ Container tests not available"
        else
            echo "⚠️ Containers not running. Skipping containerized tests."
            echo "   Run './dev.sh' or './debug.sh' first to start containers."
        fi
    else
        echo "⚠️ docker-compose not available. Skipping containerized tests."
    fi
}

# Main execution logic
FINAL_EXIT_CODE=0

case "$COMPONENT" in
    "api")
        run_api_tests
        FINAL_EXIT_CODE=$?
        ;;
    "scanner")
        run_scanner_tests
        FINAL_EXIT_CODE=$?
        ;;
    "frontend")
        run_frontend_tests
        FINAL_EXIT_CODE=$?
        ;;
    "all")
        echo "🚀 Running all tests..."
        echo "======================"
        
        # Run all component tests
        run_api_tests
        API_EXIT_CODE=$?
        
        run_scanner_tests  
        SCANNER_EXIT_CODE=$?
        
        run_frontend_tests
        FRONTEND_EXIT_CODE=$?
        
        # Run containerized tests if containers are available
        run_containerized_tests
        
        # Determine final exit code
        if [ $API_EXIT_CODE -ne 0 ] || [ $SCANNER_EXIT_CODE -ne 0 ] || [ $FRONTEND_EXIT_CODE -ne 0 ]; then
            FINAL_EXIT_CODE=1
        fi
        
        echo ""
        echo "📊 Test Summary:"
        echo "=============="
        echo "API Tests:     $([ $API_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
        echo "Scanner Tests: $([ $SCANNER_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"  
        echo "Frontend Tests: $([ $FRONTEND_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
        echo ""
        if [ $FINAL_EXIT_CODE -eq 0 ]; then
            echo "🎉 All tests passed!"
        else
            echo "💥 Some tests failed. Check the output above for details."
        fi
        ;;
esac

exit $FINAL_EXIT_CODE