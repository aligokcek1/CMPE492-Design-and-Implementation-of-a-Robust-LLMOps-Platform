# Data Model: Mock Deployment Dashboard

**Feature**: 001-mock-deployment-dashboard  
**Date**: 2025-03-10

## In-Memory Storage

All state is stored in process memory. No database. State is lost on application restart.

## Entities

### DeploymentJob

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| job_id | string (UUID) | Required, unique | Unique identifier for the deployment |
| source_type | enum | "local" \| "huggingface" | Where the model comes from |
| hardware | enum | "gpu" \| "cpu" | Target compute type |
| state | enum | See below | Current deployment phase |

### DeploymentState (enum)

| Value | Description |
|-------|-------------|
| Uploading | Simulating model upload |
| Provisioning | Simulating hardware provisioning |
| Starting Engine | Simulating engine startup |
| Serving | Deployment complete |

**State transitions**: Ordered, linear. Jobs always progress Uploading → Provisioning → Starting Engine → Serving. No failures; no rollback.

## Storage Structure

```python
# In-memory store
jobs: dict[str, DeploymentJob] = {  # job_id -> job
    "job_id": {
        "job_id": "...",
        "source_type": "local" | "huggingface",
        "hardware": "gpu" | "cpu",
        "state": "Uploading" | "Provisioning" | "Starting Engine" | "Serving"
    }
}
```

## Validation Rules

- **source_type**: Must be exactly "local" or "huggingface" (case-sensitive)
- **hardware**: Must be exactly "gpu" or "cpu" (case-sensitive)
- **job_id**: Generated server-side; never accepted from client

## Identity & Uniqueness

- **job_id**: UUID v4; generated at create time; guaranteed unique within process lifetime
- No duplicate jobs for same request; each deployment request creates exactly one job
