# Implementation Plan: Mock Deployment Dashboard

**Branch**: `001-mock-deployment-dashboard` | **Date**: 2025-03-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mock-deployment-dashboard/spec.md`

## Summary

Build a mock deployment application with a FastAPI backend and static HTML/JS dashboard. The backend exposes POST `/deploy` (accepts source_type, hardware; returns job_id; runs simulated multi-step deployment in background) and GET `/status/{job_id}` (returns current state). The frontend is a form with dropdowns and Deploy button that polls status every 2 seconds until "Serving" or error. All state is in-memory; long-running work simulated via `asyncio.sleep()`.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, uvicorn, pydantic  
**Storage**: In-memory dictionaries (no database)  
**Testing**: pytest, httpx (async client for API tests)  
**Target Platform**: Linux/macOS server; modern browsers for frontend  
**Project Type**: web-service (backend API + static frontend)  
**Performance Goals**: Deploy response <2s; status updates visible within 5s  
**Constraints**: Constitution-compliant (async, in-memory, simulated ops, static from root)  
**Scale/Scope**: Mock/demo; single process; concurrent deployments supported

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Python 3.10+ in use
- [x] All endpoints are `async def`
- [x] No database connections; in-memory dicts only
- [x] Long-running ops simulated via `asyncio.sleep()`
- [x] Static HTML/JS frontend served from root

## Project Structure

### Documentation (this feature)

```text
specs/001-mock-deployment-dashboard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── __init__.py           # Required for uvicorn backend.app.main:app
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, static mount, routes
│   ├── api/
│   │   ├── __init__.py
│   │   └── deploy.py     # POST /deploy, GET /status/{job_id}
│   ├── models/
│   │   ├── __init__.py
│   │   └── deploy.py     # Pydantic models
│   └── services/
│       ├── __init__.py
│       └── deploy.py     # Background task simulation
└── tests/
    └── __init__.py      # Add test_deploy.py when tests requested

static/
├── index.html           # Dashboard served at /
└── (TailwindCSS via CDN)
```

**Structure Decision**: Single backend app with static files at repo root. FastAPI mounts `static/` at `/`; API routes at `/deploy` and `/status/{job_id}`. No separate frontend build; HTML/JS served as-is.

## Complexity Tracking

> No Constitution Check violations. All gates pass.
