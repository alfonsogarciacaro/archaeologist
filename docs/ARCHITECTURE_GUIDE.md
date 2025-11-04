# Enterprise Architecture Setup Guide

This document provides a comprehensive guide for setting up enterprise-grade Python projects with modern tooling, containers, and observability. Use this as a template for new projects.

## 🏗️ Core Architecture Principles

### 1. **Consolidated Service Architecture**
- **Single API Service**: All functionality consolidated into one FastAPI application
- **Redis Queue**: For long-running background tasks (file processing, complex LLM analysis)
- **Vector Database**: For RAG and semantic search capabilities
- **Synchronous Operations**: Simple requests handled immediately (code scanning, status checks)

### 2. **Centralized Configuration**
- Environment variables in `.env.dev` and `.env.prod`
- Type-safe configuration with validation
- Configurable registries and external services
- Integrated scanner configuration (RAG, LLM, embeddings)

### 3. **Container Compatibility**
- RHEL UBI base images for enterprise compatibility
- Docker and Podman support via alias detection
- Optimized COPY commands with .dockerignore
- Single service deployment with Redis and VectorDB dependencies

### 4. **Modern Python Tooling**
- `uv` for cross-platform package management
- Virtual environments with proper activation
- Shared modules for code reuse
- Integrated dependencies (FastAPI + scanner functionality)

### 5. **Observability First**
- OpenTelemetry for distributed tracing
- Graceful degradation when disabled
- Business and infrastructure metrics
- Unified logging and monitoring

### 6. **Asynchronous Processing**
- **Non-blocking uploads**: Files stored immediately, processed asynchronously
- **Redis-based job queues**: Priority-based task distribution
- **Background workers**: Handle intensive processing without blocking API requests
- **Progress tracking**: Real-time status updates via API endpoints


## Test with User Stories (STORIES.md)

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


## 🏛️ Updated Architecture Overview

### Current Architecture (Consolidated)
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Single API    │───▶│ Redis Queue  │───▶│ Background     │
│   Service       │    │              │    │ Workers         │
│ (FastAPI)       │    │              │    │ (async tasks)   │
│                 │    │              │    │                 │
│ • Web API       │    │ • Priority   │    │ • File Process  │
│ • Scanner       │    │   Queue      │    │ • RAG Ingest    │
│ • LLM           │    │ • Job Status │    │ • Complex LLM   │
│ • RAG           │    │ • TTL        │    │ • Batch Ops     │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                                           │
         ▼                                           ▼
┌─────────────────┐                         ┌─────────────────┐
│   React UI      │                         │ Vector DB       │
│   (static)      │                         │ (Qdrant)        │
└─────────────────┘                         └─────────────────┘
```

### Previous Architecture (Deprecated)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Service   │───▶│   Scanner       │───▶│ External LLM    │
│                 │    │   Service       │    │ Services        │
│ • Web API       │    │ • Code Analysis │    │                 │
│ • Auth          │    │ • RAG           │    │ • Ollama        │
│ • Projects      │    │ • LLM           │    │ • OpenAI        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │ Vector DB       │    │ Redis Queue     │
│                 │    │ (Qdrant)        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ✅ Benefits of Consolidation

### **Simplified Operations**
- **Single deployment**: One service to build, deploy, and maintain
- **Unified configuration**: One set of environment variables
- **Reduced complexity**: No inter-service HTTP communication
- **Easier debugging**: Single codebase and log stream

### **Better Resource Utilization**
- **Shared connections**: Database, Redis, and vector DB connections reused
- **Memory efficiency**: Single process with shared memory
- **CPU optimization**: Better task scheduling within single process
- **Connection pooling**: Shared connection pools across all functionality

### **Maintained Scalability**
- **Horizontal scaling**: Multiple API instances with shared Redis queue
- **Async processing**: Non-blocking operations maintained
- **Background workers**: Still handle intensive tasks separately
- **Load balancing**: API instances can be load-balanced

### **Development Efficiency**
- **Single codebase**: Easier onboarding and development
- **Faster iteration**: No need to sync changes between services
- **Simplified testing**: Integration tests with single service
- **Unified CI/CD**: Single build and deployment pipeline

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
