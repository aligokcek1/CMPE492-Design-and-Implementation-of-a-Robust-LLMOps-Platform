# Tasks: Production-Grade Operations Dashboard UI

**Input**: Design documents from `specs/011-streamlit-dashboard-refactor/`  
**Branch**: `011-streamlit-dashboard-refactor`  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ui-layout.md ✅ | quickstart.md ✅

**TDD**: Tests included per constitution principle IV (Red-Green-Refactor). Write each test task before its implementation task; verify red before green.

**Remediation** (post-`/speckit-analyze`): Addresses I1–I7, S1, O1 — fleet filter before overview, sidebar before tab removal, TDD order, Grafana/FR-008/FR-012 coverage, US2/US4 split documented.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable — different files, no incomplete dependencies
- **[Story]**: User story label (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new frontend modules referenced by the implementation plan.

- [ ] T001 Create `frontend/src/ui/__init__.py` and `frontend/src/ui/` package per plan.md structure
- [ ] T002 [P] Create `frontend/src/components/sidebar.py` with `render_sidebar()`: always-visible profile/sign-out **plus** `st.expander("Settings")` wrapping `render_gcp_credentials_section` and `render_lightning_ai_credentials_section` (credential access available before main tabs are reduced to four)
- [ ] T003 [P] Create stub `frontend/src/components/fleet_overview.py` with `render_fleet_overview(counts)` export
- [ ] T004 [P] Create stub `frontend/src/components/deployment_details.py` with `render_deployment_details(dep)` export

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure UI helpers and unit tests used by US1 and US2. **No user story work until this phase completes.**

**TDD order**: Tests (T007) MUST be written and run red **before** T005 implementation.

- [ ] T007 [P] Write unit tests in `frontend/tests/unit/test_fleet_counts.py` for active/provisioning/failed mapping including `deleting`, `lost`, and `deleted` exclusion (run red before T005)
- [ ] T005 Implement `FleetCounts` dataclass, `compute_fleet_counts(deployments)`, and `filter_visible_deployments(deployments, *, show_terminated: bool)` in `frontend/src/ui/fleet_counts.py` per FR-003 and data-model.md §2
- [ ] T006 [P] Implement `status_label(status)` and `status_badge_kwargs(status)` helpers (no emoji) in `frontend/src/ui/status_display.py` per research.md §3
- [ ] T008 Run `cd frontend && pytest tests/unit/test_fleet_counts.py -q` — confirm red before T005, green after T005

**Checkpoint**: Fleet counting, visibility filter, and status display helpers tested — user story phases can begin.

---

## Phase 3: User Story 1 — Scan Fleet Health at a Glance (Priority: P1) 🎯 MVP

**Goal**: Fleet overview (Active / Provisioning / Failed) at top of **Deployments** tab; counts computed on the **same filtered list** shown below (FR-014 + FR-003).

**Independent Test**: Seed mixed statuses including `deleted` → with **Show terminated** off, three metrics match only visible non-deleted rows.

### Tests for User Story 1 (write FIRST — verify red)

- [ ] T009 [P] [US1] Create `frontend/tests/integration/test_deployments_dashboard.py` with AppTest cases: fleet metric labels present; counts match mocked visible (non-deleted) deployments per FR-003
- [ ] T010 [P] [US1] Add AppTest case: zero deployments shows 0/0/0 and professional empty-state copy (no emoji) in `frontend/tests/integration/test_deployments_dashboard.py`
- [ ] T016 [P] [US1] Add AppTest for **Show terminated** checkbox: `deleted` hidden by default, visible when checked; overview counts unchanged when toggling terminated visibility (FR-014) in `frontend/tests/integration/test_deployments_dashboard.py`
- [ ] T049 [P] [US1] Add AppTest: mocked `list_deployments` failure shows professional error copy (no stack trace; FR-012) in `frontend/tests/integration/test_deployments_dashboard.py`

### Implementation for User Story 1

**Order**: Filter → overview component → integrate on filtered list → app shell (sidebar + four tabs).

- [ ] T018 [US1] Add `st.checkbox("Show terminated", key="show_terminated")` and `filter_visible_deployments()` before rendering rows or metrics in `frontend/src/components/deployments_list.py`
- [ ] T011 [US1] Implement `render_fleet_overview(counts: FleetCounts)` using `st.columns(3)` + `st.metric` in `frontend/src/components/fleet_overview.py`
- [ ] T012 [US1] Call `filter_visible_deployments` then `compute_fleet_counts(visible)` + `render_fleet_overview` at top of `render_deployments_list()` in `frontend/src/components/deployments_list.py`
- [ ] T050 [US1] Add `st.spinner` loading state while fetching deployments and professional `st.error` on `APIError` in `frontend/src/components/deployments_list.py` (FR-012)
- [ ] T013 [US1] In `frontend/src/app.py`: wire `render_sidebar()` from `sidebar.py`; reorder `st.tabs` to four emoji-free labels — **Deployments**, **Upload Model**, **Select Model**, **Deploy** (Deployments first); remove GCP/Lightning main tabs (credentials already in sidebar per T002)
- [ ] T014 [US1] Run `cd frontend && pytest tests/integration/test_deployments_dashboard.py tests/unit/test_fleet_counts.py -q` (green)

**Checkpoint**: Fleet overview aligned with visible list; four-tab shell; credentials reachable via sidebar.

---

## Phase 4: User Story 2 — Operate Deployments from Dense Rows (Priority: P1)

**Goal**: Three-column horizontal rows with emoji-free status, text hardware labels, one-click endpoint copy, Delete/Dismiss only in collapsed row.

**Independent Test**: Running deployment row shows metadata | badge | `st.code` endpoint + Delete; no Metrics/Inference/Grafana in collapsed row. *(US2 spec scenario 2 — expand disclosure for metrics — completes in Phase 5 / US4.)*

### Tests for User Story 2 (write FIRST — verify red)

- [ ] T015 [P] [US2] Add AppTest cases in `frontend/tests/integration/test_deployments_dashboard.py`: three-column row renders; `st.code` for endpoint; no Metrics/Inference/Grafana controls in collapsed row
- [ ] T017 [P] [US2] Update `frontend/tests/integration/test_workflow.py`: replace `My Upload**` assertions with **Uploaded** text label per spec clarification

### Implementation for User Story 2

- [ ] T019 [US2] Refactor `_render_single_deployment` to `st.columns([4,2,4])` without `border=True`; use `status_display` badges in column 2 in `frontend/src/components/deployments_list.py`
- [ ] T020 [US2] Render metadata column: title, `` `hf_model_id` ``, `CPU · GKE` / `GPU · Lightning AI`, **Uploaded** label in `frontend/src/components/deployments_list.py`
- [ ] T021 [US2] Render actions column: `st.code(endpoint)` or **Pending** placeholder; **Delete** / **Dismiss** only in `frontend/src/components/deployments_list.py`
- [ ] T022 [US2] De-emphasize terminated rows (caption/muted) when Show terminated enabled in `frontend/src/components/deployments_list.py`
- [ ] T023 [US2] Run US2 tests: `cd frontend && pytest tests/integration/test_deployments_dashboard.py tests/integration/test_workflow.py -k "upload_badge or Uploaded or deployments_dashboard" -q` (green)

**Checkpoint**: Dense deployment rows — core operations layout complete.

---

## Phase 5: User Story 4 — Drill into Details Without Clutter (Priority: P2)

**Goal**: Metrics, inference, Grafana, status messages, and errors inside collapsed **Details** expander below each row.

**Independent Test**: Expand Details on running deployment → metrics + inference + Grafana link visible; collapsed row unchanged.

### Tests for User Story 4 (write FIRST — verify red)

- [ ] T024 [P] [US4] Add AppTest: **Details** expander contains metrics, inference, and **Open in Grafana** (or equivalent) link; collapsed row has no metrics panel (FR-005) in `frontend/tests/integration/test_deployments_dashboard.py`
- [ ] T025 [P] [US4] Add AppTest: long `status_message` only inside expander, not in status column caption in `frontend/tests/integration/test_deployments_dashboard.py`
- [ ] T052 [P] [US4] Add AppTest: disclosure-level inference/metrics error stays inside expander (not global page error) per spec edge case in `frontend/tests/integration/test_deployments_dashboard.py`

### Implementation for User Story 4

- [ ] T026 [US4] Implement `render_deployment_details(dep)` with `st.expander("Details", expanded=False)` in `frontend/src/components/deployment_details.py`
- [ ] T027 [US4] Move `render_deployment_metrics_panel` (including Grafana deep link) into `deployment_details.py` for `running` deployments
- [ ] T028 [US4] Move `_render_inference_panel` (rename emoji-free to **Run inference**) into `deployment_details.py`
- [ ] T029 [US4] Render `status_message` and inline errors inside expander; remove inline metrics/inference from `_render_single_deployment` in `frontend/src/components/deployments_list.py`
- [ ] T030 [US4] Invoke `render_deployment_details(dep)` immediately below each row in `frontend/src/components/deployments_list.py`
- [ ] T031 [US4] Run `cd frontend && pytest tests/integration/test_deployments_dashboard.py -q` (green)

**Checkpoint**: Verbose telemetry tucked under Details expanders.

---

## Phase 6: User Story 3 — Access Setup and Credentials from Sidebar (Priority: P2)

**Goal**: Profile/sign-out always visible; GCP + Lightning AI in **Settings**; invalid-credential banners reference Settings paths.

**Independent Test**: Save GCP credentials from Settings expander; invalid GCP blocks deploy with main-workspace banner pointing to Settings.

### Tests for User Story 3 (write FIRST — verify red)

- [ ] T032 [P] [US3] Update `frontend/tests/integration/test_credentials_workflow.py` to open **Settings** expander instead of GCP tab; assert GCP form renders
- [ ] T033 [P] [US3] Add AppTest: sidebar shows username + Sign Out without expanding Settings in `frontend/tests/integration/test_deployments_dashboard.py`
- [ ] T051 [P] [US3] Add AppTest in `frontend/tests/integration/test_workflow.py` or `test_deployments_dashboard.py`: invalid GCP credentials → Deploy attempt surfaces warning referencing **Settings → GCP Credentials** (FR-008)

### Implementation for User Story 3

- [ ] T034 [US3] Audit and harden `render_sidebar()` in `frontend/src/components/sidebar.py` for FR-006 (profile strip always visible; labeled GCP/Lightning subsections inside Settings)
- [ ] T036 [US3] Update `_render_credentials_invalid_banner()` messages to reference **Settings → GCP Credentials** / **Settings → Lightning AI** in `frontend/src/app.py`
- [ ] T037 [US3] Run `cd frontend && pytest tests/integration/test_credentials_workflow.py tests/integration/test_workflow.py -k "credentials or Settings" -q` (green)

**Checkpoint**: Credential setup and FR-008 banners validated.

---

## Phase 7: User Story 5 — Professional Navigation & Branding (Priority: P3)

**Goal**: Emoji-free chrome across titles, page config, and cross-tab copy (tabs already plain from T013; complete sweep).

**Independent Test**: Authenticated view has zero emoji in tab labels, page title, and sidebar header.

### Tests for User Story 5 (write FIRST — verify red)

- [ ] T038 [P] [US5] Add AppTest in `frontend/tests/integration/test_workflow.py`: four tabs exact labels; no emoji in `at.tabs` labels or main title
- [ ] T039 [P] [US5] Update tab assertions in `frontend/tests/integration/test_gke_deploy_workflow.py` for new tab names

### Implementation for User Story 5

- [ ] T040 [US5] Set `page_icon=None` (or neutral), `page_title="LLMOps Platform"`, emoji-free `st.title` and welcome text in `frontend/src/app.py`
- [ ] T041 [P] [US5] Remove emoji from user-facing strings in `frontend/src/components/upload.py` (empty states, cross-tab hints)
- [ ] T042 [P] [US5] Remove emoji from user-facing strings in `frontend/src/components/deploy.py` (errors, hints)
- [ ] T043 [P] [US5] Remove emoji from `frontend/src/components/deployment_metrics.py` and `frontend/src/components/gcp_credentials.py` / `lightning_ai_credentials.py` panel titles if any
- [ ] T044 [US5] Run full frontend suite: `cd frontend && pytest -q` (SC-005 zero regressions)

**Checkpoint**: Professional branding across all tabs.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Lint, manual validation, acceptance evidence.

- [ ] T045 [P] Run `cd frontend && ruff check .`
- [ ] T046 Execute manual verification per `specs/011-streamlit-dashboard-refactor/quickstart.md` (includes narrow-viewport sidebar check US3)
- [ ] T047 Capture before/after screenshots at 1920×1080 for SC-006 (10 deployments, disclosures collapsed)
- [ ] T048 Fix any remaining integration test failures from tab reorder or copy changes across `frontend/tests/integration/`

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Blocks |
|-------|------------|--------|
| 1 Setup | — | Phase 2 (T002 sidebar required before T013) |
| 2 Foundational | Phase 1 | US1, US2, US4, US3, US5 |
| 3 US1 (P1) | Phase 2 | US2 (shared `deployments_list.py`) |
| 4 US2 (P1) | US1 filter + overview (T018, T012) | US4 |
| 5 US4 (P2) | US2 row layout | — |
| 6 US3 (P2) | Phase 1 T002 sidebar | — (parallel with US4 after US2) |
| 7 US5 (P3) | US1–US4 functional | Polish |
| 8 Polish | All stories | — |

### User Story Dependencies

- **US1**: Filter (T018) **before** fleet metrics (T012); sidebar (T002) **before** four-tab cutover (T013)
- **US2**: After US1 list filter — row layout only; disclosure metrics deferred to US4 (see S1 note above)
- **US4**: After US2 row refactor
- **US3**: Sidebar scaffold in T002; US3 phase validates FR-006/FR-008
- **US5**: Final emoji sweep beyond T013 plain tab labels

### Within Each User Story

1. Tests written and failing (red)
2. Implementation tasks in dependency order documented above
3. Test run green before next story

### Parallel Opportunities

**Phase 1**: T003, T004 parallel with T002 after T001  
**Phase 2**: T007 red → T005 → T006 ∥ T008  
**US1 tests**: T009, T010, T016, T049 parallel  
**US2 tests**: T015, T017 parallel  
**US4 tests**: T024, T025, T052 parallel  
**US3 tests**: T032, T033, T051 parallel  
**US5 implementation**: T041, T042, T043 parallel  
**Cross-story**: US3 ∥ US4 after US2 checkpoint

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel): T009, T010, T016, T049
# Implementation sequence (strict):
T018 → T011 → T012 → T050 → T013 → T014
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Phase 1–2: Setup + Foundational (T007 red → T005 green)  
2. Phase 3: US1 (filter before overview; sidebar before tab cutover)  
3. Phase 4: US2 (dense rows)  
4. **STOP and VALIDATE** — operators can scan fleet health and manage deployments  

### Incremental Delivery

| Increment | Delivers |
|-----------|----------|
| MVP (US1+US2) | Filter-aligned overview + dense rows |
| +US4 | Details expanders (metrics, inference, Grafana) |
| +US3 | FR-008 banner tests + sidebar hardening |
| +US5 | Full emoji-free branding |
| Polish | SC-005/SC-006 + narrow viewport manual check |

---

## Task Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| 1 Setup | T001–T004 (4) | — |
| 2 Foundational | T005–T008 (4) | — |
| 3 US1 | T009–T014, T016, T018, T049–T050 (11) | US1 |
| 4 US2 | T015, T017, T019–T023 (7) | US2 |
| 5 US4 | T024–T031, T052 (9) | US4 |
| 6 US3 | T032–T034, T036–T037, T051 (6) | US3 |
| 7 US5 | T038–T044 (7) | US5 |
| 8 Polish | T045–T048 (4) | — |
| **Total** | **52 tasks** | |

**Parallelizable**: 24 tasks marked [P]

---

## Notes

- **I1 resolved**: T018 filter precedes T012; `compute_fleet_counts` runs on `filter_visible_deployments` output
- **I2 resolved**: T002 delivers credential UI in sidebar before T013 removes main credential tabs
- **I3 resolved**: T007 before T005 in Phase 2
- **S1**: US2 independent test excludes disclosure; US4 completes spec US2 scenario 2
- **O1 resolved**: T013 applies emoji-free tab labels at four-tab cutover
- No backend tasks — FR-013 frontend-only
- `contracts/ui-layout.md` is the authoritative layout reference
