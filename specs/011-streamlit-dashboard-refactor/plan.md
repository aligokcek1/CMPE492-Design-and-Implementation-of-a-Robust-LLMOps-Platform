# Implementation Plan: Production-Grade Operations Dashboard UI

**Branch**: `011-streamlit-dashboard-refactor` | **Date**: 2026-05-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/011-streamlit-dashboard-refactor/spec.md`

## Summary

Refactor the Streamlit LLMOps client into a production-style operations dashboard using **native Streamlit only** (no new front-end libraries). Reorganize IA to four main tabs (**Deployments** default, Upload, Select, Deploy), move GCP/Lightning credentials into a sidebar **Settings** expander with always-visible profile/sign-out, add a three-metric **fleet overview**, render deployments as dense three-column rows with copyable endpoints, and relocate metrics/inference/Grafana/errors into per-deployment **Details** expanders. No backend API changes.

---

## Technical Context

**Language/Version**: Python 3.11 (frontend only)

**Primary Dependencies**: Streamlit 1.55 (existing), `streamlit.testing.v1.AppTest`, pytest, ruff

**Storage**: N/A — presentation uses existing API responses; `st.session_state` for `show_terminated` and delete confirmations

**Testing**: `frontend/tests/integration/test_workflow.py`, `test_gke_deploy_workflow.py`, `test_credentials_workflow.py`; new `frontend/tests/unit/test_fleet_counts.py`

**Target Platform**: Browser desktop (≥1280px); wide layout via `layout="wide"`

**Project Type**: Web application (frontend presentation refactor)

**Performance Goals**: Fleet overview + list render in single Streamlit rerun; no additional API round-trips beyond existing `list_deployments`

**Constraints**:
- Native Streamlit components only (FR-009): `st.tabs`, `st.columns`, `st.metric`, `st.expander`, `st.badge`, `st.code`, `st.button`, sidebar expander
- No backend changes (FR-013)
- Emoji-free chrome (FR-002)
- Deployments tab first in `st.tabs()` for default selection (research §2)
- Row actions: copy + Delete/Dismiss only; metrics/inference/Grafana in disclosure (clarification session 2026-05-25)

**Scale/Scope**: ~6 frontend modules touched, 1 new UI helper module, ~560 lines integration tests updated; student-project deployment counts (≤20 rows)

**Assumptions**:
- Sidebar credential forms are wired in Setup (Phase 1) **before** main-area credential tabs are removed (US1), so there is no credential-access gap (analyze remediation I2).
- Fleet overview uses the same `filter_visible_deployments` output as the deployment list (analyze remediation I1).
- US3 narrow-viewport acceptance is validated manually at ~1280px via quickstart.md (analyze remediation I7).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Clean & Readable Code | ✅ PASS | Extract `fleet_counts.py` and optional `sidebar.py` / `deployment_details.py`; keep render functions <120 lines. |
| II. Security First | ✅ PASS | No new secrets; credentials stay in sidebar forms; no token logging. |
| III. Direct Framework & Library Usage | ✅ PASS | `st.badge`, `st.code` copy, `st.metric` used directly — no React/CSS framework. |
| IV. TDD Mandatory | ✅ PASS | Unit tests for `compute_fleet_counts` first; update AppTest tab/badge assertions before UI green. |
| V. Realistic & Comprehensive Testing | ✅ PASS | AppTest integration paths cover four-tab nav, fleet labels, show-terminated filter, sidebar Settings. |
| VI. Simplicity & Root Cause Resolution | ✅ PASS | Reuse `render_gcp_credentials_section` / `render_lightning_ai_credentials_section` inside sidebar expander; no API wrapper layer. |

**Post-design re-check**: ✅ All gates pass. UI contract in `contracts/ui-layout.md` bounds scope to presentation layer.

**Complexity Tracking**: No constitution violations requiring justification.

---

## Project Structure

### Documentation (this feature)

```text
specs/011-streamlit-dashboard-refactor/
├── plan.md              ← this file
├── research.md          ← Phase 0
├── data-model.md        ← Phase 1
├── quickstart.md        ← Phase 1
├── contracts/
│   └── ui-layout.md     ← Phase 1 UI contract
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app.py                              # MODIFIED: 4 tabs, sidebar import, branding, banners
│   ├── ui/
│   │   ├── __init__.py                     # NEW
│   │   ├── fleet_counts.py                 # NEW: compute_fleet_counts()
│   │   └── status_display.py               # NEW: badge label/color helpers
│   └── components/
│       ├── sidebar.py                      # NEW: profile strip + Settings expander
│       ├── fleet_overview.py               # NEW: three st.metric overview
│       ├── deployments_list.py             # MODIFIED: overview, filter, row layout, disclosures
│       ├── deployment_details.py           # NEW: disclosure body (metrics, inference, messages)
│       ├── deployment_metrics.py           # MODIFIED: called only from disclosure
│       ├── gcp_credentials.py              # UNCHANGED logic; relocated caller only
│       ├── lightning_ai_credentials.py     # UNCHANGED logic; relocated caller only
│       ├── upload.py                       # MODIFIED: emoji-free copy references
│       └── deploy.py                       # MODIFIED: emoji-free empty/error strings
└── tests/
    ├── unit/
    │   └── test_fleet_counts.py            # NEW
    └── integration/
        ├── test_workflow.py                # MODIFIED: tab labels, Uploaded badge, Deployments default
        ├── test_gke_deploy_workflow.py     # MODIFIED: tab assertions
        └── test_credentials_workflow.py    # MODIFIED: sidebar Settings path
```

**Structure Decision**: Frontend-only refactor under existing `frontend/src/` layout; small `ui/` package for testable pure functions per constitution I/IV.

---

## Implementation Phases (for `/speckit-tasks`)

### Phase A — Test scaffolding (TDD red)

1. `test_fleet_counts.py` written **before** `fleet_counts.py` (red → green).
2. Integration tests for filter-aligned overview and four-tab labels.

### Phase B — Sidebar before tab cutover (FR-006, I2)

1. `sidebar.py` in Setup: profile strip + Settings expander with credential forms **before** removing main credential tabs.
2. `app.py`: wire sidebar, then four workflow tabs (Deployments first).

### Phase C — Fleet overview & list (FR-003, FR-004, FR-011, FR-014)

1. `filter_visible_deployments` + `compute_fleet_counts` on filtered list (**before** `st.metric` overview).
2. Show-terminated checkbox in US1 (not after overview).
3. Row layout in US2; disclosures in US4 (Grafana link tested).

### Phase D — Polish & regression (SC-005, SC-006)

1. Emoji sweep across `upload.py`, `deploy.py`, empty states.
2. Run full `frontend/pytest`; manual quickstart verification.

---

## Phase 0 / Phase 1 Artifacts

| Artifact | Status |
|----------|--------|
| [research.md](./research.md) | ✅ Complete — no NEEDS CLARIFICATION |
| [data-model.md](./data-model.md) | ✅ Complete |
| [contracts/ui-layout.md](./contracts/ui-layout.md) | ✅ Complete |
| [quickstart.md](./quickstart.md) | ✅ Complete |

**Next command**: `/speckit-tasks` to generate dependency-ordered `tasks.md`.
