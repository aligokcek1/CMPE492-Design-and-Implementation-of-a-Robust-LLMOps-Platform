# Research: Mock Deployment Dashboard

**Feature**: 001-mock-deployment-dashboard  
**Date**: 2025-03-10

## Phase 0: Resolved Decisions

All technical choices are defined by the constitution and feature spec. No NEEDS CLARIFICATION items remained.

### FastAPI + asyncio Background Tasks

**Decision**: Use `asyncio.create_task()` or FastAPI's `BackgroundTasks` to run deployment simulation without blocking the response.

**Rationale**: Constitution requires async endpoints and `asyncio.sleep()` for simulation. FastAPI's `BackgroundTasks` is simple for fire-and-forget; `asyncio.create_task()` gives more control. Either satisfies constitution.

**Alternatives considered**: Celery/Redis (rejected: requires external broker, violates in-memory constraint); threading (rejected: constitution favors asyncio).

### Job ID Generation

**Decision**: Use `uuid.uuid4()` for unique job identifiers.

**Rationale**: Standard, collision-free, URL-safe when hex-encoded. No external dependency.

**Alternatives considered**: Incremental counter (simpler but less robust across restarts); nanoid (extra dependency).

### Static File Serving

**Decision**: Mount `StaticFiles` at `/` with `html=True` for index.html fallback, or mount at `/` and serve `index.html` for root path.

**Rationale**: Constitution requires serving static from root. FastAPI's `StaticFiles` supports this; need to ensure `/` returns `index.html`.

**Alternatives considered**: Separate static server (rejected: single-process requirement); SPA build (rejected: spec says no build step).

### 422 Validation Response Format

**Decision**: Use FastAPI/Pydantic default validation error format (list of `{"loc": [...], "msg": "...", "type": "..."}`).

**Rationale**: Spec requires 422 with structured error details. FastAPI returns this automatically for Pydantic validation failures.
