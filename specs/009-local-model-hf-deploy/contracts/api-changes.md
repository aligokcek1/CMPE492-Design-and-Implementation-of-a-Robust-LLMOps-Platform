# API Contract Changes: Cloud Deploy of Uploaded Models

**Branch**: `009-local-model-hf-deploy` | **Date**: 2026-05-13

All existing endpoints remain backward-compatible. Changes are purely additive (new response fields with defaults).

---

## 1. `POST /api/upload/start`

### Request (unchanged)
```
Content-Type: multipart/form-data
Authorization: Bearer <session_token>
X-Idempotency-Key: <optional>

repository_id: string   (form field)
files: file[]           (file fields)
```

### Response — changed
New field `deploy_shortcut` added.

```json
{
  "session_id": "string",
  "folder_results": [
    {
      "folder_name": "string",
      "status": "success | error",
      "error": "string | null"
    }
  ],
  "deploy_shortcut": "username/my-model | null"
}
```

`deploy_shortcut` is set to the `repository_id` value whenever the upload completes without a total failure (at least one file was transferred or the root upload succeeded). It is `null` on total failure or when no files were transferred.

---

## 2. `POST /api/deployments`

### Request (unchanged)
```json
{
  "hf_model_id": "string",
  "hardware_type": "cpu | gpu",
  "force": false
}
```

### Response — changed (202)
New field `model_origin` added. Backward compatible: existing consumers that don't read this field are unaffected.

```json
{
  "id": "string",
  "hf_model_id": "string",
  "hf_model_display_name": "string",
  "hardware_type": "cpu | gpu",
  "model_origin": "uploaded | public",
  "status": "queued | deploying | running | failed | deleting | deleted | lost",
  "status_message": "string | null",
  "endpoint_url": "string | null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### New error cases
The existing `model_not_found` (400) and `unsupported_model` (400) error codes gain one new sub-case each:

| HTTP | `code` | When |
|------|--------|------|
| `400` | `model_not_found` | Now also raised when HF Hub is unreachable within 10 s (previously only on 404) |
| `400` | `hf_hub_unreachable` | NEW — raised when HF Hub times out; message: `"HuggingFace Hub is currently unreachable, please retry."` |
| `400` | `model_access_denied` | NEW — raised when the token lacks read access to the repository (403 from HF Hub) |

---

## 3. `GET /api/deployments`

### Response — changed
Each item in the list array gains `model_origin`.

```json
[
  {
    "id": "string",
    "hf_model_id": "string",
    "hf_model_display_name": "string",
    "hardware_type": "cpu | gpu",
    "model_origin": "uploaded | public",
    "status": "string",
    "status_message": "string | null",
    "endpoint_url": "string | null",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
]
```

---

## 4. `GET /api/deployments/{deployment_id}`

### Response — changed
`model_origin` added (inherited by `DeploymentDetail` from `Deployment`).

```json
{
  "id": "string",
  "hf_model_id": "string",
  "hf_model_display_name": "string",
  "hardware_type": "cpu | gpu",
  "model_origin": "uploaded | public",
  "status": "string",
  "status_message": "string | null",
  "endpoint_url": "string | null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "gcp_project_id": "string | null",
  "gke_cluster_name": "string | null",
  "gke_region": "string | null",
  "gcp_console_url": "string | null",
  "lightning_ai_deployment_id": "string | null"
}
```

---

## 5. Internal Service Interface Changes

### `hf_models.is_supported_text_generation_model(hf_model_id, *, hf_token=None)`

**Signature change** (not an HTTP endpoint — internal Python):
```python
# Before
async def is_supported_text_generation_model(hf_model_id: str) -> tuple[bool, str, str]: ...

# After
async def is_supported_text_generation_model(
    hf_model_id: str,
    *,
    hf_token: str | None = None,
    timeout: int = 10,
) -> tuple[bool, str, str]: ...
```

Callers passing no keyword args are unaffected.

### `LightningAIProvider.deploy()`

**Protocol signature change**:
```python
# Before
async def deploy(
    self, *, hf_model_id: str, api_key: str, lightning_user_id: str
) -> tuple[str, str | None]: ...

# After
async def deploy(
    self, *, hf_model_id: str, api_key: str, lightning_user_id: str, hf_token: str = ""
) -> tuple[str, str | None]: ...
```

`FakeLightningAIProvider.deploy()` updated with the same default-arg addition. Existing test call sites passing no `hf_token` continue to work without modification.
