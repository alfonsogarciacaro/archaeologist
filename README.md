# Enterprise Code Archaeologist

An AI-powered investigation assistant that visualizes the hidden connections within complex enterprise software ecosystems.

## Quick Start

```bash
# Start all services
docker-compose up --build

# UI: http://localhost:3000
# API: http://localhost:8000
# ChromaDB: http://localhost:8001
# Scanner: http://localhost:8002
```

## The Problem

In large organizations, software systems evolve over years into tangled webs of applications, databases, and disconnected artifacts. When changes are needed, senior engineers spend countless hours on "archaeology" — manually tracing data flows and dependencies across disconnected parts of the system.

## The Solution

The Enterprise Code Archaeologist maps the impact of proposed changes across multiple repositories, databases, and artifacts. It provides:
- **Impact Visualization**: Interactive graph showing all connected components
- **Confidence Scoring**: Distinguishes between certain (literal) and probable (semantic) connections  
- **Knowledge Gap Identification**: Explicitly calls out missing information and suggests next steps

## Architecture

```
React UI → FastAPI Orchestrator → LLM Endpoint
                ↓
    Code Scanner + RAG Engine (ChromaDB) + Guardrail
```

## Development Status

This project follows a **Visual & Test-First** approach. See [CRUSH.md](./CRUSH.md) for the complete development philosophy and roadmap.

## Services

- **ui**: React frontend with interactive dependency graph
- **api**: FastAPI orchestrator that coordinates investigation
- **chromadb**: Vector database for semantic search
- **scanner**: Microservice for code scanning with ripgrep

## Testing

```bash
# Backend tests
docker-compose exec api pytest

# Frontend tests  
docker-compose exec ui npm test
```

## License

MIT