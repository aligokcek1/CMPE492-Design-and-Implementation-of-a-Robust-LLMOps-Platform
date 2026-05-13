# Implementation Plan: Cloud Deploy of Uploaded Models

**Branch**: `009-local-model-hf-deploy` | **Date**: 2026-05-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/009-local-model-hf-deploy/spec.md`

---

## Summary

Enable users to deploy models they have uploaded to their personal HuggingFace account as live inference endpoints on GKE (CPU) or Lightning AI (GPU). The feature adds universal `HF_TOKEN` injection to both deployment paths, fixes the private-model validation gate, introduces a `model_origin` field for visual differentiation in the Deployments list, and adds a one-click upload-to-deploy shortcut in the Upload tab.

---

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI 0.135, Pydantic 2.12, SQLAlchemy 2 (SQLite), huggingface_hub 1.7, lightning-sdk, litserve, Streamlit 1.55, pytest, httpx  
**Storage**: SQLite at `backend/data/llmops.db` (3 tables: `gcp_credentials`, `deployments`, `lightning_ai_credentials`). Additive column migration for `deployments.model_origin`.  
**Testing**: pytest + pytest-asyncio (backend contract tests); pytest (frontend integration tests)  
**Target Platform**: Linux server (backend); Streamlit web UI (frontend)  
**Project Type**: Web service (FastAPI backend) + Streamlit frontend  
**Performance Goals**: Pre-deployment HF Hub existence check must resolve within 10 seconds (SC-006)  
**Constraints**: Zero HF token persistence in DB, logs, or API responses (SC-005); both CPU and GPU paths must support private/gated model pull via `HF_TOKEN`

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean & Readable Code | ✅ Pass | All changes are additive to existing well-structured files; no new wrappers introduced |
| II. Security First | ✅ Pass | `HF_TOKEN` is injected transiently and never written to DB, logs, or API response body; verified in SC-005 |
| III. Direct Framework & Library Usage | ✅ Pass | `HfApi(token=hf_token)` used directly; `dep.start(env={...})` uses SDK directly; no wrapper layers |
| IV. Test-Driven Development | ✅ Pass | Contract tests must be written before implementation for all new behaviour (see task breakdown) |
| V. Realistic & Comprehensive Testing | ✅ Pass | Contract tests cover all new error codes; integration tests cover shortcut flow end-to-end |
| VI. Simplicity & Root Cause Resolution | ✅ Pass | Minimal changes: additive column, default param additions, session_state key; no over-engineering |

No gate violations.

---

## Project Structure

### Documentation (this feature)

```text
specs/009-local-model-hf-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model output
├── contracts/
│   └── api-changes.md   # Phase 1 API contract changes
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code Changes

```text
backend/
├── src/
│   ├── api/
│   │   └── deployment.py          # model_origin determination; pass hf_token to gate
│   ├── models/
│   │   ├── deployment.py          # add model_origin field to Deployment + DeploymentDetail
│   │   └── upload.py              # add deploy_shortcut field to UploadStartResponse
│   ├── db/
│   │   ├── models.py              # add model_origin column to DeploymentRow
│   │   └── migrations.py          # add additive migration for deployments.model_origin
│   └── services/
│       ├── hf_models.py           # add hf_token + timeout params; authenticated HfApi
│       ├── deployment_store.py    # add model_origin param to create()
│       ├── deployment_orchestrator.py  # pass hf_token to lightning_ai_provider.deploy()
│       ├── lightning_ai_provider.py    # add hf_token param to Protocol + RealProvider
│       └── lightning_ai_fake_provider.py  # add hf_token param to FakeProvider
└── tests/contract/
    ├── test_deployment_api.py     # new tests: private model deploy, model_origin field,
    │                              # HF unreachable error, token-authenticated gate
    └── test_upload_api.py         # new test: deploy_shortcut in response

frontend/
├── src/
│   ├── components/
│   │   ├── upload.py              # deploy shortcut button + session_state write
│   │   ├── deploy.py              # read shortcut from session_state; My Uploads hint
│   │   └── deployments_list.py    # "My Upload" badge for model_origin = "uploaded"
│   └── services/
│       └── api_client.py          # no changes needed (model_origin auto-deserialised)
└── tests/integration/
    └── test_workflow.py           # new tests: shortcut flow; My Upload badge presence
```

---

## Implementation Phases

### Phase A: Backend — Data Layer & Contracts (implement first, TDD)

**A1 — DB model + migration** (`db/models.py`, `db/migrations.py`)
- Add `model_origin: Mapped[str]` column to `DeploymentRow` with `default="public"`
- Add `("deployments", "model_origin", "ALTER TABLE deployments ADD COLUMN model_origin TEXT NOT NULL DEFAULT 'public'")` to `_ADD_COLUMN_MIGRATIONS`

**A2 — Pydantic models** (`models/deployment.py`, `models/upload.py`)
- Add `model_origin: str = "public"` to `Deployment` (inherits to `DeploymentDetail`)
- Add `deploy_shortcut: str | None = None` to `UploadStartResponse`

**A3 — Deployment store** (`services/deployment_store.py`)
- Add `model_origin: str = "public"` keyword arg to `DeploymentStore.create()`
- Pass it when constructing `DeploymentRow`

### Phase B: Backend — Service Layer

**B1 — HF model gate** (`services/hf_models.py`)
- Add `hf_token: str | None = None` and `timeout: int = 10` params to `is_supported_text_generation_model()`
- Use `HfApi(token=hf_token, timeout=timeout)` when token is provided
- Map `requests.Timeout` / timeout exceptions → return `(False, "unreachable", "HuggingFace Hub is currently unreachable, please retry.")`

**B2 — Lightning AI provider** (`services/lightning_ai_provider.py`, `services/lightning_ai_fake_provider.py`)
- Add `hf_token: str = ""` to `LightningAIProvider.deploy()` Protocol method
- In `RealLightningAIProvider._sync_deploy()`: add `env={"HF_TOKEN": hf_token}` to `dep.start()` call (only when `hf_token` is non-empty, to avoid passing empty string env var)
- Add `hf_token: str = ""` to `FakeLightningAIProvider.deploy()` (accepted, not used)

**B3 — Orchestrator** (`services/deployment_orchestrator.py`)
- In `_run_lightning_ai()`: call `_hf_token_for_user(row.user_id)` and pass result as `hf_token` to `provider.deploy()`

### Phase C: Backend — API Layer

**C1 — Deploy endpoint** (`api/deployment.py`)
- In `create_deployment`: pass `hf_token=session.hf_token` to `is_supported_text_generation_model()`
- Determine `model_origin`: `"uploaded"` if `payload.hf_model_id.split("/")[0] == session.username` else `"public"`
- Map new error returns from gate (`"unreachable"`) → HTTP 400 with `code="hf_hub_unreachable"` and the required message
- Map 403 from gate → HTTP 400 with `code="model_access_denied"`
- Pass `model_origin` to `deployment_store.create()`
- Update `_to_deployment_response()` and `_to_detail_response()` to include `model_origin` from row

**C2 — Upload endpoint** (`api/upload.py`)
- After successful upload (at least one file transferred or folder_results non-empty without all errors), set `response.deploy_shortcut = repository_id`
- Ensure idempotency replay also returns the `deploy_shortcut` (it's already stored in `response_body`)

### Phase D: Frontend

**D1 — Upload component** (`frontend/src/components/upload.py`)
- After upload success, if `result.get("deploy_shortcut")`:
  - Set `st.session_state["shortcut_deploy_model"] = result["deploy_shortcut"]`
  - Show: `st.info("✅ Model uploaded! Go to the **🚀 Deploy** tab to deploy it immediately.")`
- Show a "🚀 Deploy this model" button that sets the shortcut state and shows the prompt

**D2 — Deploy component** (`frontend/src/components/deploy.py`)
- In `render_public_repo_deploy_section()`:
  - Read `shortcut = st.session_state.pop("shortcut_deploy_model", None)` once at render time
  - Use `value=shortcut or ""` as the default for the `repo_id` text input
  - Show a success banner: `st.success(f"Ready to deploy **{shortcut}** from your upload.")` when shortcut is active
- Add a "💡 **My Uploads**: select from the **🔍 Select Existing** tab or type `username/model-name` here." hint below the text input

**D3 — Deployments list** (`frontend/src/components/deployments_list.py`)
- In the deployment row renderer, check `deployment.get("model_origin") == "uploaded"` and append `📤 **My Upload**` badge in the model name or status line

---

## Test Plan (TDD — write tests before code)

### Contract Tests (backend/tests/contract/)

**`test_deployment_api.py` additions**:
- `test_deploy_user_owned_model_sets_model_origin_uploaded` — POST deploy with `hf_model_id = f"{username}/my-model"` → response `model_origin == "uploaded"`
- `test_deploy_third_party_model_sets_model_origin_public` — POST deploy with `hf_model_id = "some-org/some-model"` → response `model_origin == "public"`
- `test_list_deployments_includes_model_origin` — GET list → each item has `model_origin`
- `test_deploy_hf_hub_unreachable_returns_400` — gate returns unreachable → HTTP 400 `hf_hub_unreachable`
- `test_deploy_model_access_denied_returns_400` — gate returns 403 → HTTP 400 `model_access_denied`

**`test_upload_api.py` additions**:
- `test_upload_start_response_includes_deploy_shortcut` — successful upload → `deploy_shortcut == repository_id`
- `test_upload_total_failure_deploy_shortcut_is_none` — total failure upload → `deploy_shortcut is None`

### Frontend Integration Tests (frontend/tests/integration/)

**`test_workflow.py` additions**:
- `test_upload_shortcut_pre_populates_deploy_tab` — upload succeeds, session_state `shortcut_deploy_model` is set to `repository_id`
- `test_my_upload_badge_shown_for_uploaded_origin` — deployment with `model_origin="uploaded"` → badge text present in rendered output
- `test_no_badge_for_public_origin` — deployment with `model_origin="public"` → no badge

---

## Complexity Tracking

No constitution violations requiring justification.
