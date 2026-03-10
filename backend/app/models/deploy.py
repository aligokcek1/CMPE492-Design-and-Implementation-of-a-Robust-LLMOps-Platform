"""Pydantic models for deployment API."""

from enum import Enum

from pydantic import BaseModel, Field


class DeploymentState(str, Enum):
    """Deployment lifecycle states."""

    UPLOADING = "Uploading"
    PROVISIONING = "Provisioning"
    STARTING_ENGINE = "Starting Engine"
    SERVING = "Serving"


class DeployRequest(BaseModel):
    """Request body for POST /deploy."""

    source_type: str = Field(..., pattern="^(local|huggingface)$")
    hardware: str = Field(..., pattern="^(gpu|cpu)$")


class DeployResponse(BaseModel):
    """Response for POST /deploy."""

    job_id: str


class StatusResponse(BaseModel):
    """Response for GET /status/{job_id}."""

    job_id: str
    state: str
