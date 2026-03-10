"""FastAPI application for mock deployment dashboard."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.deploy import router as deploy_router

app = FastAPI(title="Mock Deployment Dashboard")

# API routes (must be registered before static mount so /deploy and /status take precedence)
app.include_router(deploy_router)

# Static files - mount last so / serves index.html
static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
