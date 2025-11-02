#!/bin/bash

# Set docker command alias
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check if required commands are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker or Podman not found. Please install Docker or Podman first."
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

echo "🗄️ Starting VectorDB container at http://localhost:${VECTORDB_PORT}..."
if command -v podman-compose &> /dev/null; then
    podman-compose -f docker-compose.yml up vectordb
elif command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.yml up vectordb
else
    docker -f docker-compose.yml compose up vectordb
fi
