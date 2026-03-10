# CMPE492-Design-and-Implementation-of-a-Robust-LLMOps-Platform

This project builds an event-driven pipeline for managing LLM lifecycles. Integrating MLOps and DataOps, it creates a scalable system to automate dataset registration, fine-tuning, deployment, and monitoring. The goal is to optimize workflows for sustainable AI development through hands-on experimentation with modern tools.

## Mock Deployment Dashboard

A mock deployment application with a FastAPI backend and static HTML/JS dashboard.

**Quick start:**

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000/ for the dashboard. See [specs/001-mock-deployment-dashboard/quickstart.md](specs/001-mock-deployment-dashboard/quickstart.md) for full verification steps.
