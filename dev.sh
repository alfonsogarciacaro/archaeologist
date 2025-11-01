#!/bin/bash

# Development script for Enterprise Code Archaeologist
# This script sets up the environment for local development

echo "🔧 Setting up development environment..."

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if docker-compose or podman-compose is available
if ! command -v podman-compose &> /dev/null && ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker/Podman not found. Please install Docker or Podman first."
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
if command -v podman-compose &> /dev/null; then
    podman-compose --env-file .env.dev up --build
elif command -v docker-compose &> /dev/null; then
    docker-compose --env-file .env.dev up --build
else
    docker --env-file .env.dev compose up --build
fi

# Note: The frontend dev server will be accessible at http://localhost:3000
# API will be accessible at http://localhost:8000
# VectorDB will be accessible at http://localhost:8001