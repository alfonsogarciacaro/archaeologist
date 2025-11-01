#!/bin/bash

# Development script for Enterprise Code Archaeologist
# This script sets up the environment for local development

echo "🔧 Setting up development environment..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker or docker-compose not found. Please install Docker first."
    exit 1
fi

# Start services in development mode
echo "🚀 Starting services in development mode..."
NODE_ENV=development docker-compose up --build

# Note: The frontend dev server will be accessible at http://localhost:3000
# API will be accessible at http://localhost:8000
# ChromaDB will be accessible at http://localhost:8001