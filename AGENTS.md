# Agent Guidelines for Enterprise Code Archaeologist

## Critical Rules for Every Session

### 🚫 Service Management - DO NOT START SERVICES

**CRITICAL**: Do not start any services (api, frontend, scanner, vectordb) by yourself.

- **Always ask the user before running any service commands**
- Services are typically already running in debug mode
- Starting duplicate services will cause port conflicts and unexpected behavior
- This prevents resource conflicts and system instability

### 📝 Session Logging Requirement

**Before ending any session**: Create a session summary in `docs/sessions/`

- **Filename format**: `YYYY-MM-DD-brief-description.md`
- **Purpose**: Track progress and maintain context across sessions
- **Content**: Include objectives, accomplishments, decisions, and next steps
- **Why**: Prevents agents from reading gigantic documentation files and provides clear session history

### 🏗️ Development Guidelines

- **Visual & Test-First**: Always create visual shells and failing tests before implementation
- **API Versioning**: Use `/api/v1/` prefix for all API endpoints
- **Configuration**: Centralize in `.env.dev` and `.env.prod` files
- **Container Compatibility**: Use RHEL public images, ensure Docker/Podman compatibility
- **No .bat files**: Use shell scripts that work in Git Bash/WSL

### 🎯 Design Decision Documentation

All significant design decisions must be documented in the appropriate location:
- **Architecture decisions**: `docs/` directory files
- **Agent workflow rules**: This AGENTS.md file
- **Session outcomes**: `docs/sessions/` directory

---

## Getting Started

1. Read this file first (AGENTS.md)
2. Check `docs/VISION.md` for project context if needed
3. Review recent session summaries in `docs/sessions/` for context
4. Ask user about service status before any service operations
5. Create session summary before completing work

## Project Context

For detailed project vision, architecture, and implementation details, see:
- `docs/VISION.md` - Project vision and philosophy
- `docs/ARCHITECTURE_GUIDE.md` - Setup and best practices
- `docs/sessions/` - Recent session history

Remember: When in doubt, ask the user! Especially about service management.
