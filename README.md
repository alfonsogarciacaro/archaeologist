# Enterprise Code Archaeologist

An AI-powered investigation assistant that visualizes the hidden connections within complex enterprise software ecosystems.

## Quick Start

**For Development (with hot reload):**
```bash
./dev.sh
```

**For Production Deployment:**
```bash
./deploy.sh
```

### Access Points

- **Development**: 
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

The consolidated setup uses a unified container for the web tier with separate microservices:
- **App Container**: FastAPI + React (production) or FastAPI only (development)
- **Scanner**: Separate microservice for long-running code scanning tasks
- **ChromaDB**: Vector database for semantic search

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

## Testing

```bash
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
├── dev.sh / dev.bat          # Development startup scripts
├── deploy.sh / deploy.bat    # Production deployment scripts
├── api/                      # FastAPI backend + orchestrator
├── ui/                       # React frontend
├── scanner/                  # Code scanning microservice
└── mock_enterprise/          # Sample enterprise data
```

## License

MIT