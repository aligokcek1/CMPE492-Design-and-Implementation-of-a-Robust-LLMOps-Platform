# Data Model: Cloud Deploy of Uploaded Models

**Branch**: `009-local-model-hf-deploy` | **Date**: 2026-05-13

---

## Changed Entities

### `DeploymentRow` (SQLite — `deployments` table)

**New column**:

| Column | Type | Nullable | Default | Constraint |
|--------|------|----------|---------|------------|
| `model_origin` | `TEXT` | NOT NULL | `'public'` | `IN ('uploaded', 'public')` |

**Values**:
- `"uploaded"` — owner segment of `hf_model_id` matches the authenticated user's HF username at deploy time
- `"public"` — owner is a third party (public HF Hub model, or gated model the user does not own)

**Migration**: Additive `ALTER TABLE deployments ADD COLUMN model_origin TEXT NOT NULL DEFAULT 'public'`, applied via the existing `_ADD_COLUMN_MIGRATIONS` pattern in `db/migrations.py`. All pre-existing rows default to `"public"`, which is correct since prior features only deployed public models.

**No check constraint added via SQLAlchemy** (SQLite cannot add constraints to existing tables via `ALTER`); constraint is enforced at the application layer in `deployment_store.create()`.

---

### `UploadStartResponse` (Pydantic — `backend/src/models/upload.py`)

**New field**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `deploy_shortcut` | `str \| None` | `None` | The `repository_id` of the just-uploaded model; populated whenever the upload completes without total failure (at least one file transferred) |

Used by the frontend to pre-populate the Deploy tab's repository ID input field.

---

### `Deployment` (Pydantic — `backend/src/models/deployment.py`)

**New field**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_origin` | `str` | `"public"` | `"uploaded"` or `"public"`; matches the value stored in `DeploymentRow` |

Exposed on all three deployment response shapes: `Deployment` (list + 202 response), `DeploymentDetail` (GET by ID). The `DeploymentDetail` inherits from `Deployment`, so the field is automatically present there too.

---

## Unchanged Entities

| Entity | Reason unchanged |
|--------|-----------------|
| `GCPCredentialsRow` | No relation to model origin or upload shortcut |
| `LightningAICredentialsRow` | No relation to model origin or upload shortcut |
| `HF Token Secret` (runtime) | Not persisted; runtime env var injected at deploy time — no schema change needed |
| `FolderUploadResult` | Per-folder status already correct; `deploy_shortcut` is at the response level |

---

## State Transitions

No new states are introduced. The `model_origin` field is set once at deployment creation and never mutated.

```
                    At create_deployment time
                           │
       ┌───────────────────┴───────────────────┐
       │ hf_model_id.split("/")[0]              │
       │   == session.username ?                │
       ▼                                        ▼
  model_origin = "uploaded"           model_origin = "public"
       │                                        │
       └────────────────────┬──────────────────┘
                            │
                   Stored in DeploymentRow
                   Never updated after creation
```

---

## Frontend Session State (non-persistent)

| Key | Type | Set by | Read by | Purpose |
|-----|------|--------|---------|---------|
| `shortcut_deploy_model` | `str \| None` | `upload.py` after upload success | `deploy.py` on tab render | Pre-populates Deploy tab's repo ID input |

This is a Streamlit `st.session_state` entry, not persisted to any database.
