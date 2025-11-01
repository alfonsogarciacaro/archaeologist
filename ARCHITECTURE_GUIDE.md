# Enterprise Architecture Setup Guide

This document provides a comprehensive guide for setting up enterprise-grade Python projects with modern tooling, containers, and observability. Use this as a template for new projects.

## 🏗️ Core Architecture Principles

### 1. **Multi-Mode Development**
- **Debug Mode**: Separate processes with virtual environments for fast iteration
- **Dev Mode**: Containerized development with development configuration
- **Prod Mode**: Optimized containerized deployment

### 2. **Centralized Configuration**
- Environment variables in `.env.dev` and `.env.prod`
- Type-safe configuration with validation
- Configurable registries and external services

### 3. **Container Compatibility**
- RHEL UBI base images for enterprise compatibility
- Docker and Podman support via alias detection
- Optimized COPY commands with .dockerignore

### 4. **Modern Python Tooling**
- `uv` for cross-platform package management
- Virtual environments with proper activation
- Shared modules for code reuse

### 5. **Observability First**
- OpenTelemetry for distributed tracing
- Graceful degradation when disabled
- Business and infrastructure metrics

## 📁 Project Structure Template

```
project-name/
├── 📄 Configuration
│   ├── .env.dev              # Development environment
│   ├── .env.prod             # Production environment
│   └── .dockerignore         # Exclude from builds
├── 🐳 Containerization
│   ├── Dockerfile              # Main app container
│   ├── docker-compose.yml      # Service orchestration
│   └── service/Dockerfile     # Service containers
├── 🛠️ Development Tools
│   ├── debug.sh               # Fast local dev
│   ├── debug-stop.sh          # Stop debug services
│   ├── dev.sh                # Container dev
│   ├── deploy.sh             # Production deploy
│   └── test.sh               # Test runner
├── 🔧 Shared Code
│   ├── __init__.py
│   ├── telemetry.py          # Observability setup
│   └── middleware.py         # Common middleware
├── 🚀 Applications
│   ├── api/                  # FastAPI service
│   │   ├── app/
│   │   │   ├── main.py
│   │   └── pyproject.toml
│   ├── scanner/              # Background service
│   │   ├── main.py
│   │   ├── config.py
│   │   └── pyproject.toml
│   └── ui/                  # Frontend (if applicable)
│       ├── package.json
│       └── src/
└── 📊 Tests
    ├── api/tests/
    └── scanner/tests/
```

## ⚙️ Configuration Template

### Environment Variables (.env.dev/.env.prod)

```bash
# ==== Application Ports ====
WEB_PORT=8000
SCANNER_PORT=8002
VECTORDB_PORT=8001
UI_DEV_PORT=3000

# ==== Environment ====
NODE_ENV=development|production
COMPOSE_PROJECT_NAME=project-name

# ==== Service URLs ====
SCANNER_URL=http://localhost:${SCANNER_PORT}
VECTORDB_HOST=localhost|qdrant
VECTORDB_TYPE=qdrant
VECTORDB_COLLECTION_PREFIX=projectname
LLM_API_URL=http://localhost:11434/v1

# ==== Registry Configuration ====
CONTAINER_REGISTRY=registry.access.redhat.com|registry.company.com

# ==== Telemetry ====
# Development: OTEL_SDK_DISABLED=true
# Production: OTEL_SDK_DISABLED=false
OTEL_SERVICE_NAME=project-api
OTEL_SERVICE_VERSION=1.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_RESOURCE_ATTRIBUTES=service.name=project-api,service.version=1.0.0,deployment.environment=${NODE_ENV}
```

### Shared Module Import (main.py)

```python
# Smart shared folder detection (works in both dev and containers)
def find_shared_dir():
    """Find shared directory by navigating up from current location"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate up until we find shared folder
    while True:
        shared_path = os.path.join(current_dir, 'shared')
        if os.path.exists(shared_path):
            return shared_path
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
        current_dir = parent_dir
    
    # Fallback (shouldn't happen in proper setup)
    raise FileNotFoundError("shared directory not found")

sys.path.insert(0, find_shared_dir())

# Import shared modules
from telemetry import initialize_telemetry, get_tracer
from middleware import TracingMiddleware
```

### Configuration Class (config.py)

```python
import os
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Required fields with validation
    def __init__(self):
        # Environment
        self.NODE_ENV = os.getenv("NODE_ENV")
        if self.NODE_ENV is None:
            raise ValueError("NODE_ENV environment variable is required")
        
        # Application Ports
        self.WEB_PORT = int(os.getenv("WEB_PORT"))
        if os.getenv("WEB_PORT") is None:
            raise ValueError("WEB_PORT environment variable is required")
        
        # Telemetry Configuration
        self.OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "project-api")
        self.OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == "development"

@lru_cache()
def get_settings():
    return Settings()
```

## 🛠️ Development Scripts Template

### debug.sh - Fast Local Development

```bash
#!/bin/bash
# Docker/Podman compatibility
if ! command -v docker &> /dev/null && command -v podman &> /dev/null; then
    alias docker=podman
fi

# Check for required tools
if ! command -v uv &> /dev/null; then
    echo "❌ uv required: pip install uv"
    exit 1
fi

# Load environment
export $(cat .env.dev | grep -v '^#' | xargs)

# Create virtual environments
if [ ! -d "api/.venv" ]; then
    cd api && uv venv && cd ..
fi

# Install dependencies
cd api && uv pip sync pyproject.toml && cd ..
cd scanner && uv pip sync pyproject.toml && cd ..

# Start services in background
cd scanner && uv run python main.py &
SCANNER_PID=$!
cd ..

cd api && uv run python -m app.main &
API_PID=$!
cd ..

# Save PIDs for cleanup
echo $SCANNER_PID > .debug_scanner.pid
echo $API_PID > .debug_api.pid

echo "🚀 Debug mode started! Use ./debug-stop.sh to stop"
```

### test.sh - Universal Test Runner

```bash
#!/bin/bash
COMPONENT=${1:-"all"}

run_api_tests() {
    echo "🔌 API Tests"
    cd api
    PYTHONPATH=. uv run python -m pytest tests/ -v --tb=short -W ignore::UserWarning -W ignore::DeprecationWarning
}

run_scanner_tests() {
    echo "🔍 Scanner Tests" 
    cd scanner
    PYTHONPATH=. uv run python -m pytest -v --tb=short -W ignore::UserWarning -W ignore::DeprecationWarning
}

case "$COMPONENT" in
    "api") run_api_tests ;;
    "scanner") run_scanner_tests ;;
    "all") 
        run_api_tests
        run_scanner_tests
        ;;
esac
```

## 🐳 Containerization Template

### Dockerfile (RHEL UBI)

```dockerfile
FROM ${CONTAINER_REGISTRY}/ubi9/python-311

WORKDIR /app

# System dependencies
RUN dnf update -y && dnf install -y \
    gcc \
    ripgrep \
    curl \
    && dnf clean all

# Copy shared modules first
COPY shared/ ./shared/

# Copy and install Python dependencies
COPY api/pyproject.toml api/uv.lock ./
RUN pip install --no-cache-dir -r pyproject.toml

# Copy application code
COPY api/app/ ./app/

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "${WEB_PORT}:8000"
    environment:
      - NODE_ENV=${NODE_ENV}
      - SCANNER_URL=${SCANNER_URL}
      - WEB_PORT=${WEB_PORT}
      # ... other env vars
    volumes:
      - ./api/app:/app/app:ro
      - ./scanner:/app/scanner:ro
      - ./shared:/app/shared:ro
    depends_on:
      - scanner
      - vectordb

  scanner:
    build: 
      context: .
      dockerfile: scanner/Dockerfile
    ports:
      - "${SCANNER_PORT}:8000"
    volumes:
      - ./scanner:/app:ro
      - ./shared:/app/shared:ro
```

## 📊 Telemetry Template

### Shared Telemetry Module (shared/telemetry.py)

```python
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

class TelemetryConfig:
    def __init__(self, settings):
        self.settings = settings
        self._initialized = False
    
    def is_enabled(self):
        # Standard OTEL way to disable
        if os.getenv("OTEL_SDK_DISABLED") == "true":
            return False
        
        # Also check if endpoint is not set
        if not self.settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            return False
            
        return True
    
    def initialize_telemetry(self):
        if not self.is_enabled():
            logger.info("Telemetry disabled")
            return
        
        # Initialize tracing and metrics...
        self._initialize_tracing(resource)
        self._initialize_metrics(resource)

def get_tracer(name: str = None):
    _config = get_telemetry_config()
    if _config and _config.is_enabled():
        return trace.get_tracer(name or __name__)
    else:
        return NoOpTracer()  # Does nothing
```

### Automatic Tracing Middleware (shared/middleware.py)

```python
from starlette.middleware.base import BaseHTTPMiddleware
from telemetry import get_tracer

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        tracer = get_tracer("middleware")
        span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(span_name) as span:
            # Add HTTP attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.status_code", response.status_code)
            
            # Process request
            response = await call_next(request)
            return response
```

## 🧪 Testing Template

### Frontend Testing with Vitest

For React applications, use Vitest instead of Jest for better performance and Vite integration:

```json
// package.json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "jsdom": "^23.0.0"
  }
}
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true
  }
})
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'
```

### Test with User Stories (STORIES.md)

```markdown
# Feature: Impact Investigation

## User Story: API Health Check
As an API consumer
I want to verify the API is healthy
So that I can trust the service is available

**Acceptance Criteria:**
- GET /health returns 200 status
- Response contains "healthy" status
- Response identifies the service

---

## User Story: Code Change Impact Analysis  
As a developer
I want to investigate the impact of a proposed change
So that I can understand what systems will be affected

**Acceptance Criteria:**
- POST /investigate accepts a query string
- Returns nodes, edges, and knowledge gaps
- Identifies literal matches with 100% confidence
- Identifies semantic matches with confidence scores
- Calls out missing information as knowledge gaps

---

## User Story: Code Scanner Integration
As a developer
I want to scan codebases for literal matches
So that I can find exact references to changed components

**Acceptance Criteria:**
- POST /scan accepts query and paths
- Uses ripgrep for fast text search
- Returns file path, line number, and content
- All matches have 1.0 confidence (literal)
```

### Test Implementation (test_archaeologist.py)

```python
import pytest
from fastapi.testclient import TestClient

class TestAPIHealth:
    def test_api_health_check(self):
        """As an API consumer, I want to verify health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestImpactInvestigation:
    def test_investigate_endpoint_exists(self):
        """As a developer, I want to investigate change impact"""
        response = client.post("/investigate", json={"query": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
```

## 🚀 Deployment Template

### Production Script (deploy.sh)

```bash
#!/bin/bash
echo "🚀 Deploying to production"

# Validate environment
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod not found"
    exit 1
fi

# Build and deploy
if command -v podman-compose &> /dev/null; then
    podman-compose --env-file .env.prod up --build -d
else
    docker-compose --env-file .env.prod up --build -d
fi

# Health check
sleep 10
curl -f http://localhost:${WEB_PORT}/health || exit 1

echo "✅ Deployment successful!"
```

## 🎯 Getting Started Checklist

### For New Projects:

1. **📁 Create Structure**
   ```bash
   mkdir -p {api/app,scanner,shared,ui/src}
   touch {api/app/main.py,scanner/main.py,shared/__init__.py}
   ```

2. **⚙️ Configuration**
   - Copy `.env.dev` template
   - Create `config.py` in each service
   - Validate required environment variables

3. **🛠️ Development Tools**
   - Copy shell scripts from template
   - Make executable: `chmod +x *.sh`
   - Install `uv`: `pip install uv`

4. **📊 Observability**
   - Copy shared telemetry module
   - Add middleware to FastAPI apps
   - Configure OTEL environment variables

5. **🐳 Containerization**
   - Create Dockerfiles with UBI base
   - Set up docker-compose.yml
   - Create .dockerignore

6. **🧪 Testing**
   - Create STORIES.md with user stories
   - Write tests that match acceptance criteria
   - Set up test runner script

7. **🚀 Deployment**
   - Create production environment file
   - Set up deployment script
   - Add health checks

## 📚 Best Practices

### ✅ **Do**
- Use uv for cross-platform Python development
- Validate environment variables at startup
- Share code modules between services
- Implement graceful telemetry degradation
- Use RHEL UBI for enterprise compatibility
- Test user stories with pytest
- Use .dockerignore for smaller images

### ❌ **Don't**
- Hardcode configuration values
- Ignore deprecation warnings in production
- Copy entire project into containers
- Forget read-only volume mounts
- Assume telemetry collectors are available
- Skip error handling in distributed systems

## 🔗 Tools and Versions

### **Core Tools**
- `uv` 0.1.0+ - Python package management
- Docker/Podman - Container runtime
- Bash 4.0+ - Scripting

### **Python Stack**
- Python 3.11+ - Application runtime
- FastAPI 0.104+ - Web framework
- Pydantic 2.5+ - Data validation

### **Observability**
- OpenTelemetry 1.21+ - Distributed tracing
- Jaeger/Tempo - Telemetry collector
- Grafana - Metrics visualization

### **Infrastructure**
- RHEL UBI 9+ - Base images
- Node.js 18+ - Frontend builds
- Chrome/Firefox - Application access
**COPY Strategy:**
- `COPY shared/ ./shared/` - Shared modules first (for caching)
- `COPY api/app/ ./app/` - Only app code (excludes tests)
- `COPY scanner/main.py .` - Specific files (not whole dir)
- **Benefits**: Smaller images, excludes test code in production

**For Development with Tests:**
```dockerfile
# Use volume mounts for local development
volumes:
  - ./api/app:/app/app           # Includes tests for dev
  - ./api/tests:/app/tests       # Mount test directory
```
