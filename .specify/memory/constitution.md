<!--
Sync Impact Report:
- Version change: N/A → 1.0.0 (initial ratification)
- Modified principles: N/A (initial creation)
- Added sections: Core Principles, Technology Stack, Development Constraints, Governance
- Removed sections: N/A
- Templates requiring updates:
  - plan-template.md: ✅ Constitution Check gates align (Python 3.10+, FastAPI, async, in-memory)
  - spec-template.md: ✅ No mandatory section changes required
  - tasks-template.md: ✅ Task categorization reflects mock backend constraints
  - Follow-up TODOs: None
-->

# LLMOps Platform Mock Backend Constitution

## Core Principles

### I. Python 3.10+ Runtime
All backend code MUST target Python 3.10 or newer. Use type hints and modern syntax (e.g., `match`/`case`, improved error messages). Rationale: Ensures compatibility with current tooling and enables async/await patterns required for the mock backend.

### II. Asynchronous Endpoints (NON-NEGOTIABLE)
Every API endpoint MUST be declared with `async def`. No synchronous route handlers. Rationale: Enables non-blocking I/O and proper simulation of long-running operations without blocking the event loop.

### III. In-Memory State Only
The application MUST NOT connect to any external database. All persistent state MUST be stored in in-memory dictionaries (or equivalent structures like `dict`, `defaultdict`). State resets on process restart. Rationale: Keeps the mock backend self-contained, portable, and free of infrastructure dependencies.

### IV. Simulated Long-Running Operations
Operations that would normally be long-running (e.g., model uploads, GCP GPU provisioning, fine-tuning jobs) MUST be simulated using `asyncio.sleep()`. No real external API calls or resource provisioning. Rationale: Allows testing of async flows and timeout handling without real infrastructure.

### V. Static Frontend Serving
The FastAPI application MUST serve a static HTML/JS frontend from the root directory (e.g., `"/"` or `"/index.html"`). Use `StaticFiles` or equivalent to mount static assets. Rationale: Single-process deployment for development and demos; frontend and backend run together.

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Storage**: In-memory dictionaries only
- **Frontend**: Static HTML/JS served from repository root
- **Simulation**: `asyncio.sleep()` for all long-running work

## Development Constraints

- No database drivers, ORMs, or connection pools
- No real cloud API integrations (GCP, AWS, etc.)
- All endpoints MUST return JSON or serve static files
- Use Pydantic models for request/response validation
- Prefer `httpx.AsyncClient` for any internal HTTP calls (if needed)

## Governance

This constitution governs the mock FastAPI backend for the LLMOps Platform. All PRs and reviews MUST verify compliance with the principles above. Amendments require documentation, rationale, and a version bump. Use the feature specification and implementation plan for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2025-03-10 | **Last Amended**: 2025-03-10
