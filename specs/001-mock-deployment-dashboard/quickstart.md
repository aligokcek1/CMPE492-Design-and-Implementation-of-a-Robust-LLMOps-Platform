# Quickstart: Mock Deployment Dashboard

**Feature**: 001-mock-deployment-dashboard

## Prerequisites

- Python 3.10+
- pip or uv

## Setup

```bash
# From repository root
pip install -r requirements.txt   # or: uv pip install -r requirements.txt
```

## Run

```bash
# From repository root
uvicorn backend.app.main:app --reload
```

Application runs at `http://127.0.0.1:8000`.

## Verify

1. **Dashboard**: Open `http://127.0.0.1:8000/` in a browser. You should see the deployment form.
2. **Deploy**: Select Source Type (local/huggingface), Hardware (gpu/cpu), click Deploy. Status should update until "Serving".
3. **API**: `curl -X POST http://127.0.0.1:8000/deploy -H "Content-Type: application/json" -d '{"source_type":"local","hardware":"gpu"}'` returns `{"job_id":"..."}`.
4. **Status**: `curl http://127.0.0.1:8000/status/{job_id}` returns `{"job_id":"...","state":"..."}`.

## Project Layout

```
backend/
  app/
    main.py       # FastAPI app
    api/deploy.py # Routes
    models/       # Pydantic models
    services/     # Background task logic
static/
  index.html      # Dashboard (TailwindCSS via CDN)
```
