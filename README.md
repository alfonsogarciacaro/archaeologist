# Enterprise Code Archaeologist

An AI-powered investigation assistant that visualizes the hidden connections within complex enterprise software ecosystems.

## Quick Start

**⚠️ Important: Before running, ensure your environment variables are up to date by checking the `.env.dev` and `.env.prod` files. The application will fail to start if required environment variables are missing.**

**For Debug Mode (fastest local development with separate processes):**
```bash
./debug.sh      # Start all services as separate processes
./debug-stop.sh # Stop debug services
```

**For Development Mode (containerized with hot reload):**
```bash
./dev.sh
```

**For Production Deployment:**
```bash
./deploy.sh
```

### Access Points

- **Debug Mode**: 
  - Frontend: http://localhost:3000 (React dev server)
  - API: http://localhost:8000
  - Scanner: http://localhost:8002
  - ChromaDB: http://localhost:8001

- **Development Mode**: 
  - Frontend: http://localhost:3000 (React dev server)
  - API: http://localhost:8000
  - Scanner: http://localhost:8002
  - ChromaDB: http://localhost:8001

- **Production**:
  - Application: http://localhost:8000 (serves both UI and API)
  - Scanner: http://localhost:8002 (internal service)
  - ChromaDB: http://localhost:8001

## The Problem

In large organizations, software systems evolve over years into tangled webs of applications, databases, and disconnected artifacts. When changes are needed, senior engineers spend countless hours on "archaeology" — manually tracing data flows and dependencies across disconnected parts of the system.

## The Solution

The Enterprise Code Archaeologist maps the impact of proposed changes across multiple repositories, databases, and artifacts. It provides:
- **Impact Visualization**: Interactive graph showing all connected components
- **Confidence Scoring**: Distinguishes between certain (literal) and probable (semantic) connections  
- **Knowledge Gap Identification**: Explicitly calls out missing information and suggests next steps

## Architecture

The consolidated setup uses a unified container for the web tier with separate microservices. All containers are based on RHEL UBI (Universal Base Image) for enterprise compatibility:
- **App Container**: FastAPI + React (production) or FastAPI only (development) - RHEL UBI9 Python
- **Scanner**: Separate microservice for long-running code scanning tasks - RHEL UBI9 Python  
- **ChromaDB**: Vector database for semantic search - RHEL UBI9 Minimal

All Docker and docker-compose files are compatible with both Docker and Podman for RHEL environments.

```
Production:  React (static) + FastAPI → Scanner → ChromaDB
Development: React (dev server) → FastAPI → Scanner → ChromaDB
```

## Resource Optimization

The new approach reduces memory usage by:
- **Consolidated web tier**: Single container for API + UI
- **Separate scanner**: Non-blocking, long-running code searches
- **Efficient static serving**: FastAPI serves production React build

## Development Status

This project follows a **Visual & Test-First** approach. See [CRUSH.md](./CRUSH.md) for the complete development philosophy and roadmap.

## Registry Configuration

The project supports configurable container registries through environment variables. Add `CONTAINER_REGISTRY` to your `.env.dev` or `.env.prod` files:

```bash
# Default (public RHEL registry)
CONTAINER_REGISTRY=registry.access.redhat.com

# Internal company registry example
CONTAINER_REGISTRY=registry.company.com/internal
```

Note: Python (pip) and Node.js (npm) package registries can be configured at the machine level using standard pip/npm configuration methods.

## Testing

```bash
# Debug mode tests (faster iteration)
# Backend tests
cd api && source .venv/bin/activate && pytest

# Scanner tests
cd scanner && source .venv/bin/activate && pytest

# Frontend tests
cd ui && npm test

# Containerized tests (Docker/Podman)
# Backend tests
docker-compose exec app pytest

# Scanner tests
docker-compose exec scanner pytest

# Frontend tests (development mode)
cd ui && npm test
```

## Project Structure

```
enterprise-archaeologist/
├── Dockerfile                 # Unified web container (API + UI build)
├── docker-compose.yml         # All services orchestrated
├── .env.dev                   # Development environment variables
├── .env.prod                  # Production environment variables
├── debug.sh                   # Debug mode startup (separate processes)
├── debug-stop.sh              # Debug mode stop script
├── dev.sh                     # Development mode startup (containers)
├── deploy.sh                  # Production deployment script
├── api/                       # FastAPI backend + orchestrator
├── ui/                        # React frontend
├── scanner/                   # Code scanning microservice
└── mock_enterprise/           # Sample enterprise data
```

## License

MIT