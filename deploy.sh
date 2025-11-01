#!/bin/bash

# Production deployment script for Enterprise Code Archaeologist
# This script builds and deploys the application in production mode

echo "🚀 Deploying Enterprise Code Archaeologist in production mode..."

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if docker-compose or podman-compose is available
if ! command -v podman-compose &> /dev/null && ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker/Podman not found. Please install Docker or Podman first."
    exit 1
fi

# Load production environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
    echo "✅ Loaded .env.prod"
else
    echo "❌ Error: .env.prod file not found!"
    exit 1
fi

# Build and deploy in production mode
echo "🏗️ Building and starting production services..."
if command -v podman-compose &> /dev/null; then
    podman-compose --env-file .env.prod up --build -d
elif command -v docker-compose &> /dev/null; then
    docker-compose --env-file .env.prod up --build -d
else
    docker --env-file .env.prod compose up --build -d
fi

echo "✅ Application deployed successfully!"
echo "🌐 Access the application at: http://localhost:8000"
echo "🔍 API health check: http://localhost:8000/health"

# Show running containers
echo ""
echo "📦 Running containers:"
if command -v podman-compose &> /dev/null; then
    podman-compose ps
elif command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi