#!/bin/bash

# Production deployment script for Enterprise Code Archaeologist
# This script builds and deploys the application in production mode

echo "🚀 Deploying Enterprise Code Archaeologist in production mode..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker or docker-compose not found. Please install Docker first."
    exit 1
fi

# Build and deploy in production mode
echo "🏗️ Building and starting production services..."
NODE_ENV=production docker-compose up --build -d

echo "✅ Application deployed successfully!"
echo "🌐 Access the application at: http://localhost:8000"
echo "🔍 API health check: http://localhost:8000/health"

# Show running containers
echo ""
echo "📦 Running containers:"
docker-compose ps