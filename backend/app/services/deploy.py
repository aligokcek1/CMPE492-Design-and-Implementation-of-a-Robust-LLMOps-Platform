"""Deployment service with in-memory store and simulated background tasks."""

import asyncio
import uuid
from typing import Any

from backend.app.models.deploy import DeploymentState


# In-memory job store: job_id -> {job_id, source_type, hardware, state}
jobs: dict[str, dict[str, Any]] = {}


async def run_deployment_simulation(job_id: str) -> None:
    """Simulate multi-step deployment with asyncio.sleep()."""
    states = [
        DeploymentState.UPLOADING,
        DeploymentState.PROVISIONING,
        DeploymentState.STARTING_ENGINE,
        DeploymentState.SERVING,
    ]
    for state in states:
        if job_id in jobs:
            jobs[job_id]["state"] = state.value
        await asyncio.sleep(1.5)  # Simulate ~1.5s per step


def start_deployment(source_type: str, hardware: str) -> str:
    """Create job, spawn background task, return job_id."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "source_type": source_type,
        "hardware": hardware,
        "state": DeploymentState.UPLOADING.value,
    }
    asyncio.create_task(run_deployment_simulation(job_id))
    return job_id


def get_status(job_id: str) -> dict[str, Any] | None:
    """Return job dict or None if not found."""
    return jobs.get(job_id)
