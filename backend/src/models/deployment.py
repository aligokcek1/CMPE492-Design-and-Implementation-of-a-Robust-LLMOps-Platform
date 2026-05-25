from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Feature 004 / 005 / 006 — personal-repo mock deployment models               #
# Kept unchanged for backward compatibility with existing contract tests.      #
# --------------------------------------------------------------------------- #


class ResourceType(str, Enum):
    CPU = "CPU"
    GPU = "GPU"


class DeploymentStatus(str, Enum):
    pending = "pending"
    mock_success = "mock_success"


class MockDeployment(BaseModel):
    model_repository: str
    resource_type: ResourceType
    deployment_status: DeploymentStatus = DeploymentStatus.pending


class MockDeploymentRequest(BaseModel):
    model_repository: str
    resource_type: ResourceType


class MockDeploymentResponse(BaseModel):
    status: str
    message: str


# --------------------------------------------------------------------------- #
# Feature 007 — real GKE deployment models                                     #
# --------------------------------------------------------------------------- #


class GkeDeploymentStatus(str, Enum):
    queued = "queued"
    deploying = "deploying"
    running = "running"
    failed = "failed"
    deleting = "deleting"
    deleted = "deleted"
    lost = "lost"


class DeployRequest(BaseModel):
    hf_model_id: str = Field(
        ..., description="HuggingFace model repository ID, e.g. Qwen/Qwen3-1.7B"
    )
    hardware_type: Literal["cpu", "gpu"] = Field(
        ...,
        description="Target hardware: 'cpu' routes to GKE/TGI-CPU; 'gpu' routes to Lightning AI/vLLM.",
    )
    force: bool = Field(default=False, description="Bypass the duplicate-model confirmation.")


class Deployment(BaseModel):
    id: str
    hf_model_id: str
    hf_model_display_name: str
    hardware_type: str
    model_origin: str = "public"
    status: GkeDeploymentStatus
    status_message: str | None = None
    endpoint_url: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentDetail(Deployment):
    # CPU-specific fields (None for GPU deployments)
    gcp_project_id: str | None = None
    gke_cluster_name: str | None = None
    gke_region: str | None = None
    gcp_console_url: str | None = None
    # GPU-specific field (None for CPU deployments)
    lightning_ai_deployment_id: str | None = None
