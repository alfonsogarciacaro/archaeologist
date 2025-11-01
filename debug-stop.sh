#!/bin/bash

# Stop script for debug mode
# This script stops all debug services and cleans up

echo "🛑 Stopping debug environment..."

# Stop processes using saved PIDs
if [ -f .debug_scanner.pid ]; then
    SCANNER_PID=$(cat .debug_scanner.pid)
    if kill -0 $SCANNER_PID 2>/dev/null; then
        echo "🔍 Stopping Scanner (PID: $SCANNER_PID)..."
        kill $SCANNER_PID
    fi
    rm -f .debug_scanner.pid
fi

if [ -f .debug_api.pid ]; then
    API_PID=$(cat .debug_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "🌐 Stopping API (PID: $API_PID)..."
        kill $API_PID
    fi
    rm -f .debug_api.pid
fi

if [ -f .debug_ui.pid ]; then
    UI_PID=$(cat .debug_ui.pid)
    if kill -0 $UI_PID 2>/dev/null; then
        echo "⚛️ Stopping UI (PID: $UI_PID)..."
        kill $UI_PID
    fi
    rm -f .debug_ui.pid
fi

# Stop ChromaDB container
echo "🗄️ Stopping ChromaDB container..."
docker-compose down

echo "✅ Debug environment stopped successfully!"