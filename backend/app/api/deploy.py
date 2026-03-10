"""Deployment API routes."""

from fastapi import APIRouter, HTTPException

from backend.app.models.deploy import DeployRequest, DeployResponse, StatusResponse
from backend.app.services import deploy as deploy_service

router = APIRouter(prefix="", tags=["deploy"])


@router.post("/deploy", response_model=DeployResponse)
async def deploy(request: DeployRequest) -> DeployResponse:
    """Initiate deployment; returns job_id immediately; runs simulation in background."""
    job_id = deploy_service.start_deployment(
        source_type=request.source_type,
        hardware=request.hardware,
    )
    return DeployResponse(job_id=job_id)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    """Return current deployment state for job_id."""
    job = deploy_service.get_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(job_id=job["job_id"], state=job["state"])
