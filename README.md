# Enterprise Code Archaeologist

An AI-powered investigation assistant that visualizes the hidden connections within complex enterprise software ecosystems.

## Quick Start

**⚠️ Important: Before running, ensure your environment variables are up to date by checking the `.env.dev` and `.env.prod` files. The application will fail to start if required environment variables are missing.**

**⚠️ Requirements**: This project uses `uv` for Python package management. Install with `pip install uv` or visit https://github.com/astral-sh/uv.

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

## Telemetry Configuration

The API and Scanner services are instrumented with OpenTelemetry for distributed tracing and metrics. Telemetry configuration is controlled through environment variables:

```bash
# Service identification
OTEL_SERVICE_NAME=archaeologist-api
OTEL_SERVICE_VERSION=1.0.0

# Exporter configuration (OTLP endpoint for your telemetry collector)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Resource attributes
OTEL_RESOURCE_ATTRIBUTES=service.name=archaeologist-api,service.version=1.0.0,deployment.environment=development
```

**Telemetry Features:**
- **Automatic Instrumentation**: FastAPI, HTTP requests, and HTTPX calls are automatically traced
- **Manual Instrumentation**: Key operations like investigations and scans include custom spans
- **Error Tracking**: Failed operations are captured with detailed error information
- **Metrics**: Ready for custom metrics collection
|- **Graceful Degradation**: When telemetry is disabled, no-op tracers ensure application continues normally
n**Disabling Telemetry for Development/Testing:**
1. **Standard Way**: Set `OTEL_SDK_DISABLED=true` (recommended by OpenTelemetry)
2. **Alternative**: Leave `OTEL_EXPORTER_OTLP_ENDPOINT` empty
3. **Environment Override**: Set in `.env.dev` file for local development


**Note**: You'll need to configure an OTLP-compatible telemetry collector (like Jaeger, Tempo, or a commercial service) to receive the telemetry data.

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
# Run all tests
./test.sh

# Run specific component tests
./test.sh api          # API tests only
./test.sh scanner      # Scanner tests only  
./test.sh frontend     # Frontend tests only

# Manual testing (if needed)
# Debug mode tests (faster iteration)
cd api && uv run python -m pytest

cd scanner && uv run python -m pytest

cd ui && npm test

# Containerized tests (Docker/Podman)
docker-compose exec app pytest
docker-compose exec scanner pytest
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
├── test.sh                    # Test runner for all components
├── api/                       # FastAPI backend + orchestrator
├── ui/                        # React frontend
├── scanner/                   # Code scanning microservice
└── mock_enterprise/           # Sample enterprise data
```

## License

MIT