# Deployment API Contract

**Base URL**: `/` (relative to application root)

## POST /deploy

Initiates a deployment. Returns immediately with `job_id`; deployment runs in background.

### Request

**Content-Type**: `application/json`

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| source_type | string | Yes | "local", "huggingface" | Model source |
| hardware | string | Yes | "gpu", "cpu" | Target hardware |

**Example**:
```json
{
  "source_type": "local",
  "hardware": "gpu"
}
```

### Response: 200 OK

**Content-Type**: `application/json`

| Field | Type | Description |
|-------|------|-------------|
| job_id | string | Unique deployment identifier (UUID) |

**Example**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Response: 422 Unprocessable Entity

Invalid or missing parameters. Structured error details in body (FastAPI/Pydantic format).

**Example**:
```json
{
  "detail": [
    {
      "loc": ["body", "source_type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## GET /status/{job_id}

Returns the current deployment state for a job.

### Path Parameters

| Name | Type | Description |
|------|------|-------------|
| job_id | string | Deployment job identifier |

### Response: 200 OK

**Content-Type**: `application/json`

| Field | Type | Description |
|-------|------|-------------|
| job_id | string | Job identifier |
| state | string | Current state: "Uploading", "Provisioning", "Starting Engine", "Serving" |

**Example**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "Provisioning"
}
```

### Response: 404 Not Found

Job does not exist (unknown `job_id`).

**Example**:
```json
{
  "detail": "Job not found"
}
```
