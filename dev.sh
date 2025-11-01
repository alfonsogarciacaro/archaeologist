#!/bin/bash

# Development script for Enterprise Code Archaeologist
# This script sets up the environment for local development

echo "🔧 Setting up development environment..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker or docker-compose not found. Please install Docker first."
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

# Start services in development mode
echo "🚀 Starting services in development mode..."
docker-compose --env-file .env.dev up --build

# Note: The frontend dev server will be accessible at http://localhost:3000
# API will be accessible at http://localhost:8000
# ChromaDB will be accessible at http://localhost:8001