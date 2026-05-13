# Tasks: Cloud Deploy of Uploaded Models

**Input**: Design documents from `specs/009-local-model-hf-deploy/`  
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/api-changes.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.  
**TDD**: Contract tests are written FIRST (marked before implementation tasks) per Constitution Principle IV.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Verify baseline before any changes.

- [ ] T001 Verify existing backend test suite passes clean: `cd backend && pytest` (baseline checkpoint)
- [ ] T002 Verify existing frontend test suite passes clean: `cd frontend && pytest` (baseline checkpoint)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data layer and Pydantic model changes that ALL three user stories depend on. Must complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Add `model_origin: Mapped[str]` column (`NOT NULL DEFAULT 'public'`) to `DeploymentRow` in `backend/src/db/models.py`
- [ ] T004 Add additive column migration `("deployments", "model_origin", "ALTER TABLE deployments ADD COLUMN model_origin TEXT NOT NULL DEFAULT 'public'")` to `_ADD_COLUMN_MIGRATIONS` in `backend/src/db/migrations.py`
- [ ] T005 [P] Add `model_origin: str = "public"` field to `Deployment` Pydantic model in `backend/src/models/deployment.py`
- [ ] T006 [P] Add `deploy_shortcut: str | None = None` field to `UploadStartResponse` Pydantic model in `backend/src/models/upload.py`

**Checkpoint**: DB schema and response models updated — user story implementation can now begin.

---

## Phase 3: User Story 1 — Deploy Uploaded Model to Cloud (Priority: P1) 🎯 MVP

**Goal**: Users can deploy private/gated HF models (user-uploaded or third-party gated) to GKE CPU and Lightning AI GPU; `HF_TOKEN` is injected universally; `model_origin` is stored and returned in all deployment responses.

**Independent Test**: POST `/api/deployments` with a model whose owner matches the session username → response contains `model_origin: "uploaded"`; POST with a third-party model → `model_origin: "public"`. Verify Lightning AI `dep.start()` receives `env={"HF_TOKEN": ...}` in tests.

### Contract Tests for User Story 1

> **Write these tests FIRST. Run them — they MUST FAIL before implementation.**

- [ ] T007 [P] [US1] Contract test `test_deploy_user_owned_model_sets_model_origin_uploaded`: POST `/api/deployments` with `hf_model_id = f"{username}/private-model"` → `model_origin == "uploaded"` in `backend/tests/contract/test_deployment_api.py`
- [ ] T008 [P] [US1] Contract test `test_deploy_third_party_model_sets_model_origin_public`: POST `/api/deployments` with `hf_model_id = "org/some-model"` → `model_origin == "public"` in `backend/tests/contract/test_deployment_api.py`
- [ ] T009 [P] [US1] Contract test `test_deploy_hf_hub_unreachable_returns_400`: mock gate to return `(False, "unreachable", "HuggingFace Hub is currently unreachable, please retry.")` → HTTP 400 with `code="hf_hub_unreachable"` in `backend/tests/contract/test_deployment_api.py`
- [ ] T010 [P] [US1] Contract test `test_deploy_model_access_denied_returns_400`: mock gate to return `(False, "access_denied", ...)` → HTTP 400 with `code="model_access_denied"` in `backend/tests/contract/test_deployment_api.py`
- [ ] T011 [P] [US1] Contract test `test_list_deployments_each_item_has_model_origin`: GET `/api/deployments` → each item in list contains `model_origin` field in `backend/tests/contract/test_deployment_api.py`
- [ ] T034 [P] [US1] Contract test `test_get_deployment_by_id_includes_model_origin`: GET `/api/deployments/{id}` → response body contains `model_origin` field (covers M2 — DeploymentDetail contract) in `backend/tests/contract/test_deployment_api.py`
- [ ] T035 [P] [US1] Contract test `test_deployment_response_does_not_contain_hf_token`: POST `/api/deployments` → assert none of the response fields (`id`, `hf_model_id`, `status_message`, `model_origin`, etc.) contain the string value of the session HF token; assert `DeploymentRow` has no column named `hf_token` (covers C1 — SC-005 security / Constitution II MUST) in `backend/tests/contract/test_deployment_api.py`
- [ ] T036 [P] [US1] Contract test `test_gpu_deploy_public_model_injects_hf_token_to_provider`: POST `/api/deployments` with `hf_model_id = "org/public-model"` (third-party, `model_origin="public"`, `hardware_type="gpu"`) → `FakeLightningAIProvider.deploy()` receives a non-empty `hf_token` kwarg (covers M1 — FR-002 universal injection) in `backend/tests/contract/test_deployment_api.py`
- [ ] T037 [P] [US1] Contract test `test_deploy_hf_hub_slow_times_out_within_10s`: patch `HfApi.model_info` to sleep 15s; POST `/api/deployments` → response arrives in ≤12 seconds with HTTP 400 `code="hf_hub_unreachable"` (covers H2 — SC-006 10s timeout) in `backend/tests/contract/test_deployment_api.py`
- [ ] T038 [P] [US1] Contract test `test_deployment_status_message_human_readable_on_token_revoked`: simulate orchestrator status-message update with raw vLLM/TGI exit text containing `401 Unauthorized`; assert `status_message` shown to user does not expose raw stack trace and contains a human-readable hint about token validity (covers H1 — FR-007 runtime pull failure) in `backend/tests/contract/test_deployment_api.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Update `is_supported_text_generation_model()` to accept `hf_token: str | None = None` and `timeout: int = 10`; use `HfApi(token=hf_token, timeout=timeout)` when token provided; map timeout/unreachable exceptions to `(False, "unreachable", "HuggingFace Hub is currently unreachable, please retry.")` in `backend/src/services/hf_models.py`
- [ ] T013 [P] [US1] Add `hf_token: str = ""` keyword arg to `LightningAIProvider.deploy()` Protocol method in `backend/src/services/lightning_ai_provider.py`
- [ ] T014 [P] [US1] Add `hf_token: str = ""` keyword arg to `FakeLightningAIProvider.deploy()` (accept, do not use) in `backend/src/services/lightning_ai_fake_provider.py`
- [ ] T015 [US1] Update `RealLightningAIProvider._sync_deploy()` to pass `env={"HF_TOKEN": hf_token}` to `dep.start()` when `hf_token` is non-empty in `backend/src/services/lightning_ai_provider.py` (depends on T013)
- [ ] T016 [US1] Add `model_origin: str = "public"` keyword arg to `DeploymentStore.create()` and pass it when constructing `DeploymentRow` in `backend/src/services/deployment_store.py` (depends on T003, T004)
- [ ] T017 [US1] Update `DeploymentOrchestrator._run_lightning_ai()` to call `_hf_token_for_user(row.user_id)` and pass result as `hf_token=` to `provider.deploy()` in `backend/src/services/deployment_orchestrator.py` (depends on T013, T014, T015)
- [ ] T018 [US1] Update `create_deployment()` in `backend/src/api/deployment.py`: pass `hf_token=session.hf_token` to `is_supported_text_generation_model()`; determine `model_origin` by comparing `hf_model_id.split("/")[0]` to `session.username`; map `"unreachable"` gate return → HTTP 400 `hf_hub_unreachable`; map 403 / `"access_denied"` → HTTP 400 `model_access_denied`; pass `model_origin` to `deployment_store.create()` (depends on T012, T016)
- [ ] T019 [US1] Update `_to_deployment_response()` and `_to_detail_response()` in `backend/src/api/deployment.py` to read `model_origin` from `DeploymentRow` and include it in the `Deployment` / `DeploymentDetail` response (depends on T005, T018)

**Checkpoint**: User Story 1 fully functional — private models can be deployed to both CPU and GPU; `model_origin` appears on all deployment responses; all new contract tests pass.

---

## Phase 4: User Story 2 — Shortcut from Upload to Deploy (Priority: P2)

**Goal**: After a successful upload, the user sees a "Deploy this model" prompt and navigating to the Deploy tab shows the uploaded model's repository ID pre-populated in the input field.

**Independent Test**: Call `POST /api/upload/start` with valid files → response contains `deploy_shortcut == repository_id`. In frontend: after upload succeeds, `st.session_state["shortcut_deploy_model"]` is set to the repository ID; the Deploy tab's repo ID text input shows that value as default.

### Contract Tests for User Story 2

> **Write these tests FIRST. Run them — they MUST FAIL before implementation.**

- [ ] T020 [P] [US2] Contract test `test_upload_start_response_includes_deploy_shortcut`: mock upload succeeds → `deploy_shortcut == repository_id` in response in `backend/tests/contract/test_upload_api.py`
- [ ] T021 [P] [US2] Contract test `test_upload_total_failure_deploy_shortcut_none`: all folder uploads fail → `deploy_shortcut is None` (or root-only upload with no folders also sets shortcut) in `backend/tests/contract/test_upload_api.py`

### Implementation for User Story 2

- [ ] T022 [US2] Update `start_upload()` in `backend/src/api/upload.py` to set `response.deploy_shortcut = repository_id` when upload completes without total failure (depends on T006)
- [ ] T023 [US2] Update `render_upload_section()` in `frontend/src/components/upload.py`: after upload success, set `st.session_state["shortcut_deploy_model"] = result["deploy_shortcut"]` when `deploy_shortcut` is present; display `st.info("✅ Model uploaded! Go to the **🚀 Deploy** tab to deploy it immediately.")`
- [ ] T024 [US2] Update `render_public_repo_deploy_section()` in `frontend/src/components/deploy.py`: pop `st.session_state.get("shortcut_deploy_model")` at render start; use as default value for the repo ID text input; show `st.success(f"Ready to deploy **{shortcut}** from your upload.")` banner when shortcut is active (depends on T023)
- [ ] T025 [P] [US2] Frontend integration test `test_upload_shortcut_sets_session_state`: simulate successful upload response with `deploy_shortcut`; assert `st.session_state["shortcut_deploy_model"]` is set to the repository ID in `frontend/tests/integration/test_workflow.py`

**Checkpoint**: User Story 2 functional — upload shortcut sets session state; Deploy tab reads and pre-populates the repo ID field.

---

## Phase 5: User Story 3 — Distinguish Uploaded Models in UI (Priority: P3)

**Goal**: The Select tab's model list shows user's models under a "📤 My Uploads" heading; the Deployments list shows a "📤 My Upload" badge on each row where `model_origin == "uploaded"`.

**Independent Test**: Render `render_model_selector()` → section header "My Uploads" is present. Render a deployment row with `model_origin="uploaded"` → "My Upload" text appears in the output. Render a row with `model_origin="public"` → no "My Upload" text.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Update `render_model_selector()` in `frontend/src/components/upload.py` to display `st.markdown("### 📤 My Uploads")` header above the model selector dropdown to visually distinguish user's own repos from public HF Hub models
- [ ] T027 [US3] Update the deployment row renderer in `frontend/src/components/deployments_list.py` to append `· 📤 **My Upload**` inline badge when `deployment.get("model_origin") == "uploaded"` (depends on T019)
- [ ] T028 [P] [US3] Frontend integration test `test_my_upload_badge_shown_for_uploaded_origin`: provide deployment dict with `model_origin="uploaded"`; assert "My Upload" in rendered output in `frontend/tests/integration/test_workflow.py`
- [ ] T029 [P] [US3] Frontend integration test `test_no_badge_for_public_origin`: provide deployment dict with `model_origin="public"`; assert "My Upload" not in rendered output in `frontend/tests/integration/test_workflow.py`

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T030 [P] Run full backend contract test suite and confirm all new tests pass: `cd backend && pytest`
- [ ] T031 [P] Run full frontend integration test suite and confirm all new tests pass: `cd frontend && pytest`
- [ ] T032 [P] Run backend linter and fix any ruff violations: `cd backend && ruff check .`
- [ ] T033 [P] Run frontend linter and fix any ruff violations: `cd frontend && ruff check .`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — run immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — no dependency on US2 or US3
- **Phase 4 (US2)**: Depends on Phase 2 — no dependency on US1 or US3
- **Phase 5 (US3)**: Depends on Phase 2 + Phase 3 (needs `model_origin` in API response T019)
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — independent of US2 and US3
- **US2 (P2)**: Starts after Phase 2 — independent of US1 and US3
- **US3 (P3)**: Starts after Phase 2 + T019 (needs `model_origin` in API response for badge rendering)

### Within Each User Story

- Contract tests MUST be written first and verified to FAIL (red phase)
- DB/model changes before service layer (T003–T006 before T015–T019)
- Service layer before API layer (T012–T017 before T018)
- Backend API before frontend (T018–T019 before T023–T025)
- Implementation must pass all contract tests before story is marked complete

### Parallel Opportunities

- T005 and T006 (Phase 2 model additions) can run in parallel
- T007–T011, T034–T038 (US1 contract tests) can all be written in parallel
- T012, T013, T014 can be written in parallel (different files)
- T020, T021 (US2 contract tests) can run in parallel with T007–T011
- T026, T028, T029 can run in parallel within US3
- T030–T033 (Polish) all run in parallel

---

## Parallel Example: Phase 2

```bash
# These two model additions have no dependencies on each other:
Task: "Add model_origin to Deployment model in backend/src/models/deployment.py"  # T005
Task: "Add deploy_shortcut to UploadStartResponse in backend/src/models/upload.py"  # T006
```

## Parallel Example: User Story 1 Contract Tests

```bash
# All contract tests can be written at the same time:
Task: "test_deploy_user_owned_model_sets_model_origin_uploaded"          # T007
Task: "test_deploy_third_party_model_sets_model_origin_public"           # T008
Task: "test_deploy_hf_hub_unreachable_returns_400"                       # T009
Task: "test_deploy_model_access_denied_returns_400"                      # T010
Task: "test_list_deployments_each_item_has_model_origin"                 # T011
Task: "test_get_deployment_by_id_includes_model_origin"                  # T034
Task: "test_deployment_response_does_not_contain_hf_token"               # T035 (SC-005 / Constitution II)
Task: "test_gpu_deploy_public_model_injects_hf_token_to_provider"        # T036 (FR-002 universal injection)
Task: "test_deploy_hf_hub_slow_times_out_within_10s"                     # T037 (SC-006 timing)
Task: "test_deployment_status_message_human_readable_on_token_revoked"   # T038 (FR-007 runtime failure)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: verify baseline passes
2. Complete Phase 2: DB column + Pydantic models (T003–T006)
3. Complete Phase 3: US1 contract tests then implementation (T007–T019, T034–T038)
4. **STOP and VALIDATE**: `cd backend && pytest` — all new tests pass
5. Demo: deploy a private user-uploaded model end-to-end

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Private model deploy works + `model_origin` in responses
3. US2 → Upload-to-deploy shortcut works
4. US3 → Visual badges and My Uploads label
5. Polish → Clean lint + full test pass

### Parallel Team Strategy

Once Phase 2 is done:
- **Developer A**: US1 (backend services + API)
- **Developer B**: US2 (backend upload endpoint + frontend shortcut)
- Both unblock US3 which is the frontend-only display layer

---

## Notes

- [P] tasks = different files, no inter-task dependencies
- TDD is mandatory per Constitution Principle IV — no implementation task should be started until its contract test exists and fails
- `model_origin` defaults to `"public"` in DB migration so all pre-existing deployment rows remain valid
- `HF_TOKEN` must never appear in `DeploymentRow`, API response body, or any log line (SC-005) — enforced by T035 contract test
- T036 verifies HF_TOKEN injection applies universally (FR-002), including for `model_origin="public"` GPU deployments
- T037 verifies the 10s pre-deploy check timeout is enforced (SC-006)
- T038 verifies FR-007: runtime token-revoked errors surface as human-readable status messages
- The `shortcut_deploy_model` session state key is consumed with `pop()` in the Deploy tab so it only pre-populates once per upload
