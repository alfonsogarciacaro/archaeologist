#!/bin/bash

# Deployment script for Enterprise Code Archaeologist
# Usage: ./deploy.sh [prod]
# If "prod" is specified, uses .env.prod, otherwise uses .env.dev

# Determine which environment to use
ENVIRONMENT=${1:-dev}
ENV_FILE=".env.$ENVIRONMENT"

echo "🚀 Deploying Enterprise Code Archaeologist in $ENVIRONMENT mode..."

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if docker-compose or podman-compose is available
if ! command -v podman-compose &> /dev/null && ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker/Podman not found. Please install Docker or Podman first."
    exit 1
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
    echo "✅ Loaded $ENV_FILE"
else
    echo "❌ Error: $ENV_FILE file not found!"
    exit 1
fi

# Build and deploy
echo "🏗️ Building and starting $ENVIRONMENT services..."
if command -v podman-compose &> /dev/null; then
    podman-compose --env-file "$ENV_FILE" up --build -d
elif command -v docker-compose &> /dev/null; then
    docker-compose --env-file "$ENV_FILE" up --build -d
else
    docker --env-file "$ENV_FILE" compose up --build -d
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