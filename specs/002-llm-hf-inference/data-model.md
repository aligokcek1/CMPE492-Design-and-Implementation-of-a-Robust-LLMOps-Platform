# Data Model: LLM Inference App with Hugging Face Integration

**Feature**: 002-llm-hf-inference
**Date**: 2026-03-14

## Core Entities

### 1. Hugging Face Account (Configuration)
Represents the user's connection status. This is not stored in a database but rather evaluated at runtime via the environment.
- `hf_token` (String): The User Access Token stored in `.env`.
- `is_connected` (Boolean): Derived state; true if the token is present and valid when tested against the HF API.
- `username` (String): The HF username associated with the token (fetched and cached in memory).

### 2. Model Source
An enum/literal representing where a model originates before deployment.
- `LOCAL_PC`: A file uploaded directly from the user's machine (size <= 500MB).
- `USER_HF_REPO`: A repository already existing under the user's HF account.
- `PUBLIC_HF_REPO`: A reference (ID) to a public repository not owned by the user.

### 3. Model Registry (Local Cache Database)
A SQLite table (`models`) used to cache metadata for UI responsiveness and track deployment status.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing internal ID |
| `name` | String | Not Null | User-friendly name of the model |
| `source_type` | String | Enum (`Model Source`) | Where the model originated |
| `hf_repo_id` | String | Not Null | The Hugging Face Repository ID (e.g., `username/inference-app-model` or `public-user/model`) |
| `is_deployed` | Boolean | Default `False` | Tracks if the model has been deployed to the mocked GCP environment |
| `deployed_at` | DateTime | Nullable | Timestamp of deployment |
| `last_synced` | DateTime | Not Null | Last time this metadata was verified against the HF API |

**Validation Rules:**
- `hf_repo_id` must be a valid Hugging Face repository identifier format (`namespace/repo-name`).
- Local file uploads must not exceed 500MB before creating the corresponding registry entry and HF repo.
- If `source_type` is `PUBLIC_HF_REPO`, the app must verify the `hf_repo_id` is accessible via the HF API before saving to the registry.

### State Transitions (Model Lifecycle)
1. **Unregistered** -> **Registered (Not Deployed)**: User uploads a local file (creates HF repo) OR selects a public repo (stores reference).
2. **Registered (Not Deployed)** -> **Deployed**: User clicks "Deploy to Cloud" for a model in the registry. `is_deployed` becomes True.
3. **Deployed** -> **Inference Ready**: Implicit state. Any deployed model can immediately be queried in the mocked UI.
