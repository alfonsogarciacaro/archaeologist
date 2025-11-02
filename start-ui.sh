#!/bin/bash

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

echo "⚛️ Starting UI development server..."
cd ui && npm start
