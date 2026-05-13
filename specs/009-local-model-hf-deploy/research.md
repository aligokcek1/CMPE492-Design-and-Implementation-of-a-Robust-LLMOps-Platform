# Research: Cloud Deploy of Uploaded Models

**Branch**: `009-local-model-hf-deploy` | **Date**: 2026-05-13

---

## Decision 1: HF_TOKEN Injection — GKE CPU Path

**Decision**: No code change needed to `vllm_manifest.py`. The GKE path already injects `HF_TOKEN` universally.

**Rationale**: `vllm_manifest.generate()` already accepts an `hf_token` parameter and bakes a Kubernetes `Secret` + two env var references (`HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`) into the generated manifest. The orchestrator's `_hf_token_for_user()` helper already fetches the session token and passes it to `generate()`. This covers all deployments — public, gated, and private — with zero additional code on the CPU path.

**The only GKE-path blocker** is that `hf_models.is_supported_text_generation_model()` uses an unauthenticated `HfApi()`, causing 403 ("private repo, only public repos can be deployed") for any model whose owner is the authenticated user. Fix: pass `hf_token` to this function so it can read private repo metadata.

**Alternatives considered**: Adding a separate "skip validation for user-owned models" code path. Rejected because an authenticated token check is simpler, covers gated public models too, and keeps a single consistent pre-deploy validation function.

---

## Decision 2: HF_TOKEN Injection — Lightning AI GPU Path

**Decision**: Update `LightningAIProvider.deploy()` protocol and `RealLightningAIProvider._sync_deploy()` to accept an `hf_token: str` parameter and pass it as an environment variable to `dep.start()`.

**Rationale**: The Lightning AI Python SDK's `Deployment.start()` accepts an `env` keyword argument (dict of `str → str`) that gets injected into the deployment container's environment. The vLLM image (`vllm/vllm-openai:latest`) reads `HF_TOKEN` from the environment to authenticate model downloads. Passing `env={"HF_TOKEN": hf_token}` to `dep.start()` is the correct mechanism.

**Token safety**: The token is passed as a runtime env var inside the SDK call. It is never stored in the `DeploymentRow`, never logged by the orchestrator, and never serialised to JSON in any API response — satisfying SC-005 (zero credentials leakage).

**Alternatives considered**:
- Embedding `export HF_TOKEN=...` in the `command` string — rejected because the command string may surface in Lightning AI logs, violating SC-005.
- Using Lightning AI Secrets API for persistent secret storage — rejected because it introduces a new credential-management surface; transient env vars are simpler and already sufficient.

**Flow change**: `DeploymentOrchestrator._run_lightning_ai()` calls `_hf_token_for_user(row.user_id)` (already used by the CPU path) and passes the result as `hf_token` to `provider.deploy()`.

---

## Decision 3: Private Model Validation Gate

**Decision**: Add an optional `hf_token: str | None` parameter to `hf_models.is_supported_text_generation_model()`. When provided, create an authenticated `HfApi(token=hf_token)` and use it for the `model_info()` call.

**Rationale**: The current gate uses `token=None`, which makes the HF Hub return 403 for any private or gated model. With the authenticated token, private user-owned models and gated public models (e.g., Llama) are readable, allowing pipeline_tag validation to proceed normally. The API layer (`create_deployment`) passes `session.hf_token` to this function so all deployments benefit.

**Edge case — gated model without approval**: If the authenticated user hasn't yet accepted the gating agreement on HF Hub, the call returns 403. This correctly surfaces as a "token lacks read access" error (FR-003 case b) — consistent, no special-casing needed.

**Alternatives considered**: Skipping pipeline_tag validation for user-owned models entirely. Rejected because the gate prevents accidental deployment of non-text-generation models (e.g., image classifiers), which would fail in TGI/vLLM with cryptic errors.

---

## Decision 4: `model_origin` Determination

**Decision**: At `create_deployment` time, compare `hf_model_id.split("/")[0]` against `session.username`. Match → `"uploaded"`, no match → `"public"`. Store in a new `model_origin` column on `DeploymentRow`.

**Rationale**: This owner-segment comparison is a O(1) string check that works for both the upload-shortcut path and manual entry. The username is already available in the session object (`session.username` is the HF username from `verify_hf_token`). No extra HF API call is needed.

**Migration strategy**: Additive `ALTER TABLE deployments ADD COLUMN model_origin TEXT NOT NULL DEFAULT 'public'`. This follows the existing `_ADD_COLUMN_MIGRATIONS` pattern in `db/migrations.py` and is backward-compatible with existing rows (which are all public-model deployments defaulting to `"public"`).

---

## Decision 5: Deploy Shortcut — Frontend Tab Pre-population

**Decision**: On upload success, store `st.session_state["shortcut_deploy_model"] = repository_id`. The Deploy tab's public-repo text input reads this value as its initial content.

**Rationale**: Streamlit does not support programmatic tab switching. The best compatible approach is pre-populating the relevant input on the target tab using `session_state`. The upload component shows a prominent message ("✅ Model uploaded! Switch to the **Deploy** tab to deploy it.") so the user knows to navigate there. The Deploy tab detects the prefilled value and shows the shortcut context clearly.

**Alternatives considered**: Displaying a full mini-deploy form inside the Upload tab results. Rejected because it duplicates hardware-selection UI and credential-check logic already in the Deploy tab.

---

## Decision 6: "My Upload" Badge in Deployments List

**Decision**: In `deployments_list.py`, render a `📤 My Upload` inline badge (via `st.markdown`) next to the model ID for any row where `model_origin == "uploaded"`.

**Rationale**: A purely additive visual indicator requires no new filtering UI, satisfies SC-004 ("at a glance without extra clicks"), and is forward-compatible if a filter selector is added later.

---

## Decision 7: Pre-Deploy Check Timeout

**Decision**: Add a `timeout` parameter (default `10`) to `is_supported_text_generation_model()` and propagate it to the executor-wrapped `model_info()` call via `httpx_timeout` on the `HfApi` constructor.

**Rationale**: The `HfApi` constructor accepts a `timeout` parameter. Setting it to 10 seconds ensures that on HF Hub outages, the pre-deploy check fails within 10 seconds with a caught `requests.Timeout` / `httpx.ReadTimeout`, which the API layer maps to the "HuggingFace Hub is currently unreachable, please retry." message (FR-003 case c).

---

## Summary Table

| Unknown | Decision | Key Files Changed |
|---------|----------|-------------------|
| GPU HF_TOKEN injection | `dep.start(env={"HF_TOKEN": token})` in Lightning AI SDK | `lightning_ai_provider.py`, `deployment_orchestrator.py` |
| Private model validation | Authenticated `HfApi(token=hf_token)` in gate | `hf_models.py`, `api/deployment.py` |
| `model_origin` storage | Additive column, owner-segment comparison | `db/models.py`, `db/migrations.py`, `deployment_store.py` |
| Deploy shortcut UX | `session_state` pre-population, Deploy tab reads it | `upload.py`, `deploy.py` |
| Pre-deploy timeout | `HfApi(timeout=10)` | `hf_models.py` |
| "My Upload" badge | `model_origin` field in API responses + `st.markdown` badge | `deployments_list.py` |
