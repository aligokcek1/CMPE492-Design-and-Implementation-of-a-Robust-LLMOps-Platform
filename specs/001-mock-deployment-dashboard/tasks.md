# Tasks: Mock Deployment Dashboard

**Input**: Design documents from `/specs/001-mock-deployment-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec; omitted. Add via `/speckit.tasks` with test request if needed.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `static/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure: backend/, backend/__init__.py, backend/app/, backend/app/api/, backend/app/models/, backend/app/services/, backend/tests/, static/ with __init__.py in each package (backend/__init__.py required for uvicorn backend.app.main:app)
- [x] T002 Create requirements.txt at repo root with fastapi, uvicorn, pydantic
- [x] T003 [P] Configure ruff in pyproject.toml or ruff.toml for backend/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create FastAPI app in backend/app/main.py with app instance
- [x] T005 Mount StaticFiles for static/ directory at / in backend/app/main.py (ensure / serves index.html)
- [x] T006 Add API router mounting structure in backend/app/main.py (routes to be registered in US1)

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Initiate Model Deployment (Priority: P1) 🎯 MVP

**Goal**: Backend API accepts deploy requests, returns job_id, runs simulated deployment in background; status endpoint returns current state.

**Independent Test**: `curl -X POST http://127.0.0.1:8000/deploy -H "Content-Type: application/json" -d '{"source_type":"local","hardware":"gpu"}'` returns job_id; `curl http://127.0.0.1:8000/status/{job_id}` returns state progressing to Serving.

### Implementation for User Story 1

- [x] T007 [P] [US1] Create Pydantic models in backend/app/models/deploy.py: DeployRequest (source_type, hardware), DeployResponse (job_id), StatusResponse (job_id, state), DeploymentState enum (Uploading, Provisioning, Starting Engine, Serving)
- [x] T008 [US1] Create in-memory job store (dict) and deploy service in backend/app/services/deploy.py: start_deployment() creates job, spawns background task with asyncio.sleep() per state, run_deployment_simulation() updates state
- [x] T009 [US1] Implement POST /deploy and GET /status/{job_id} in backend/app/api/deploy.py with async def handlers, 404 for unknown job_id, 422 for validation errors
- [x] T010 [US1] Register deploy router in backend/app/main.py; place include_router() before app.mount() in source order so /deploy and /status take precedence over static catch-all

**Checkpoint**: User Story 1 complete - API testable via curl

---

## Phase 4: User Story 2 - Monitor Deployment via Dashboard (Priority: P2)

**Goal**: Dashboard at / with form, Deploy button, status polling, loading indicator until Serving or error.

**Independent Test**: Open http://127.0.0.1:8000/, select options, click Deploy; see status updates until Serving; form stays enabled for multiple deployments.

### Implementation for User Story 2

- [x] T011 [US2] Create static/index.html with form: Source Type dropdown (local, huggingface), Hardware dropdown (gpu, cpu), Deploy button
- [x] T012 [US2] Add TailwindCSS via CDN in static/index.html
- [x] T013 [US2] Add JavaScript in static/index.html: on Deploy click POST /deploy, receive job_id, poll GET /status/{job_id} every 2s, display state text and loading spinner, stop when state is Serving or status returns error (e.g. 404), show error message on failure; form remains enabled during polling

**Checkpoint**: User Stories 1 and 2 complete - full flow works in browser

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements across user stories

- [x] T014 [P] Run quickstart.md validation: install deps, start app, verify dashboard and API per quickstart steps
- [x] T015 Update README.md with run instructions and link to quickstart

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3–4)**: Depend on Foundational
  - US1: No dependency on US2
  - US2: Depends on US1 (API must exist for dashboard to call)
- **Polish (Phase 5)**: Depends on US1 and US2 complete

### User Story Dependencies

- **User Story 1 (P1)**: Start after Foundational - independent
- **User Story 2 (P2)**: Start after US1 - dashboard calls deploy and status APIs

### Within Each User Story

- Models before services
- Services before endpoints
- US1: T007 → T008 → T009 → T010
- US2: T011 → T012 → T013 (T011/T012 can overlap; T013 needs T011)

### Parallel Opportunities

- T002 and T003 can run in parallel after T001
- T007 is [P] within US1
- T014 is [P] in Polish

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test API via curl
5. Deploy/demo backend-only if needed

### Incremental Delivery

1. Setup + Foundational → app runs, static mount ready
2. Add User Story 1 → API works (MVP!)
3. Add User Story 2 → Full dashboard flow
4. Polish → Quickstart validated

---

## Notes

- [P] = parallelizable
- [US1]/[US2] = story traceability
- No test tasks (spec did not request)
- Commit after each task or logical group
