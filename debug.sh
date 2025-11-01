#!/bin/bash

# Debug mode for Enterprise Code Archaeologist
# This script runs services as separate processes for faster development iteration
# with virtual environments and a container only for ChromaDB

echo "🔧 Setting up debug environment (separate processes)..."

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if required commands are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker or Podman not found. Please install Docker or Podman first."
    exit 1
fi

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

# Start ChromaDB container only
echo "🗄️ Starting ChromaDB container..."
if command -v podman-compose &> /dev/null; then
    podman-compose -f docker-compose.yml up chromadb -d
elif command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.yml up chromadb -d
else
    docker -f docker-compose.yml compose up chromadb -d
fi

# Check if ChromaDB is running
if command -v podman-compose &> /dev/null; then
    if ! podman-compose -f docker-compose.yml ps chromadb | grep -q "Up"; then
        echo "❌ Failed to start ChromaDB"
        exit 1
    fi
elif command -v docker-compose &> /dev/null; then
    if ! docker-compose -f docker-compose.yml ps chromadb | grep -q "Up"; then
        echo "❌ Failed to start ChromaDB"
        exit 1
    fi
else
    if ! docker compose ps chromadb | grep -q "Up"; then
        echo "❌ Failed to start ChromaDB"
        exit 1
    fi
fi

echo "✅ ChromaDB started at http://localhost:${CHROMADB_PORT}"

# Setup virtual environments and install dependencies if needed
echo "🐍 Setting up Python environments..."

# API virtual environment
if [ ! -d "api/.venv" ]; then
    echo "Creating API virtual environment..."
    cd api && uv venv && cd ..
fi

# Install API dependencies
echo "Installing API dependencies..."
cd api && uv pip sync pyproject.toml && cd ..

# Scanner virtual environment
if [ ! -d "scanner/.venv" ]; then
    echo "Creating Scanner virtual environment..."
    cd scanner && uv venv && cd ..
fi

# Install Scanner dependencies
echo "Installing Scanner dependencies..."
cd scanner && uv pip sync pyproject.toml && cd ..

# UI dependencies
if [ ! -d "ui/node_modules" ]; then
    echo "📦 Installing UI dependencies..."
    cd ui && npm install
    cd ..
fi

echo "🚀 Starting debug services (separate processes)..."

# Start Scanner service (background)
echo "🔍 Starting Scanner service..."
cd scanner && uv run python -m app.main &
SCANNER_PID=$!
echo "Scanner PID: $SCANNER_PID"

# Start API service (background)
echo "🌐 Starting API service..."
cd api && uv run python -m app.main &
API_PID=$!
echo "API PID: $API_PID"

# Start UI dev server (background)
echo "⚛️ Starting React development server..."
cd ui && PORT=$UI_DEV_PORT npm start &
UI_PID=$!
echo "UI PID: $UI_PID"

echo ""
echo "✅ Debug environment started successfully!"
echo "🌐 Frontend: http://localhost:${UI_DEV_PORT}"
echo "🔌 API: http://localhost:${WEB_PORT}"
echo "🔍 Scanner: http://localhost:${SCANNER_PORT}"
echo "🗄️ ChromaDB: http://localhost:${CHROMADB_PORT}"
echo ""
echo "📋 Process IDs:"
echo "   - Scanner: $SCANNER_PID"
echo "   - API: $API_PID"
echo "   - UI: $UI_PID"
echo ""
echo "💡 To stop all services, run: ./debug-stop.sh"
echo "🔍 To view logs, use: tail -f api/logs.txt scanner/logs.txt"

# Save PIDs to file for cleanup
echo "$SCANNER_PID" > .debug_scanner.pid
echo "$API_PID" > .debug_api.pid
echo "$UI_PID" > .debug_ui.pid

# Wait for user to stop
trap 'echo "Stopping services..."; kill $SCANNER_PID $API_PID $UI_PID 2>/dev/null; if command -v podman-compose &> /dev/null; then podman-compose down; elif command -v docker-compose &> /dev/null; then docker-compose down; else docker compose down; fi; rm -f .debug_*.pid; exit' INT

echo "Press Ctrl+C to stop all services"
wait