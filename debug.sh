#!/bin/bash

# Debug mode for Enterprise Code Archaeologist
# This script runs services as separate processes for faster development iteration
# with virtual environments and a container only for ChromaDB

echo "🔧 Setting up debug environment (separate processes)..."

# Check if required commands are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python first."
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
docker-compose -f docker-compose.yml up chromadb -d

# Check if ChromaDB is running
if ! docker-compose -f docker-compose.yml ps chromadb | grep -q "Up"; then
    echo "❌ Failed to start ChromaDB"
    exit 1
fi

echo "✅ ChromaDB started at http://localhost:${CHROMADB_PORT}"

# Setup virtual environments and install dependencies if needed
echo "🐍 Setting up Python environments..."

# API virtual environment
if [ ! -d "api/.venv" ]; then
    echo "Creating API virtual environment..."
    cd api && python3 -m venv .venv
    cd .venv && source bin/activate && pip install --upgrade pip && pip install -r requirements.txt
    cd ../..
fi

# Scanner virtual environment
if [ ! -d "scanner/.venv" ]; then
    echo "Creating Scanner virtual environment..."
    cd scanner && python3 -m venv .venv
    cd .venv && source bin/activate && pip install --upgrade pip && pip install -r requirements.txt
    cd ../..
fi

# UI dependencies
if [ ! -d "ui/node_modules" ]; then
    echo "📦 Installing UI dependencies..."
    cd ui && npm install
    cd ..
fi

echo "🚀 Starting debug services (separate processes)..."

# Start Scanner service (background)
echo "🔍 Starting Scanner service..."
cd scanner && source .venv/bin/activate && python main.py &
SCANNER_PID=$!
cd ..
echo "Scanner PID: $SCANNER_PID"

# Start API service (background)
echo "🌐 Starting API service..."
cd api && source .venv/bin/activate && python -m app.main &
API_PID=$!
cd ..
echo "API PID: $API_PID"

# Start UI dev server (background)
echo "⚛️ Starting React development server..."
cd ui && PORT=$UI_DEV_PORT npm start &
UI_PID=$!
cd ..
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
trap 'echo "Stopping services..."; kill $SCANNER_PID $API_PID $UI_PID 2>/dev/null; docker-compose down; rm -f .debug_*.pid; exit' INT

echo "Press Ctrl+C to stop all services"
wait