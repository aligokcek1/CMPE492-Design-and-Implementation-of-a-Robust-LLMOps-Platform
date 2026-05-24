# Implementation Plan: Deployment Metrics Monitoring with Prometheus and Grafana

**Branch**: `010-prometheus-grafana-monitoring` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/010-prometheus-grafana-monitoring/spec.md`

## Summary

Add hybrid deployment monitoring: native Streamlit summary stats + trend charts in the **Deployments** tab, plus an **Open in Grafana** signed deep link for advanced drill-down. Track **TTFT**, **average throughput**, and **hardware utilization** for **running** CPU (GKE/TGI) and GPU (Lightning AI) deployments.

Each deployment receives an isolated Prometheus scrape job (label-scoped metric namespace) and a paired Grafana datasource on a shared Grafana instance. The backend instruments `inference_proxy.forward()` with `prometheus-client` for TTFT/throughput, dynamically registers scrape targets for CPU TGI `/metrics` endpoints, and exposes `GET /api/deployments/{id}/metrics` plus signed Grafana redirect URLs. Metrics UI and Grafana links are removed immediately on delete; raw data is retained 7 days backend-only for operators.

---

## Technical Context

**Language/Version**: Python 3.11 (backend + frontend)

**Primary Dependencies**:
- Backend: FastAPI 0.135, Pydantic 2.12, SQLAlchemy 2.x, SQLite, `prometheus-client` (new — proxy-side metrics), `httpx` (existing — PromQL + Grafana HTTP API), `cryptography` (existing — HMAC signing secret reuse pattern)
- Frontend: Streamlit 1.55 (existing), native `st.line_chart` / `st.metric` for in-app charts (no Grafana iframes)
- Infrastructure (dev/ops): Prometheus 2.x + Grafana 11.x via `docker-compose.monitoring.yml` at repo root

**Storage**: SQLite at `backend/data/llmops.db` — new `deployment_monitoring` table tracks scrape job name, Grafana datasource UID, dashboard UID, provision status, and decommission schedule. Time-series data lives in Prometheus (not SQLite).

**Testing**: pytest, pytest-asyncio, httpx. Real SQLite per test. `FakePrometheusProvisioner` + `FakeGrafanaProvisioner` + canned PromQL responses for contract tests — no real Prometheus/Grafana calls in `pytest`.

**Target Platform**: Linux server (backend + Prometheus/Grafana stack), browser (Streamlit frontend).

**Performance Goals**:
- Metrics API responds ≤ 2 s for 7-day range queries under dev load
- In-app charts reflect activity from the last 60 s within 2 min (SC-002) — Prometheus scrape interval 15 s
- Grafana signed link generation ≤ 500 ms

**Constraints**:
- Hybrid UX: native Streamlit charts only; Grafana via explicit link (FR-005a)
- Per-deployment Prometheus scrape job + per-deployment Grafana datasource (clarified topology)
- Signed deep links for Grafana — no separate Grafana login (FR-009a)
- GPU hardware series labeled N/A when provider metrics absent — no proxy-inferred GPU values (FR-003a)
- No post-delete user metrics access; 7-day backend retention only (FR-014/FR-014a)
- TTFT/throughput measured at inference proxy boundary; v1 TTFT = time-to-first-response-byte for non-streaming CPU/GPU paths (see spec Assumptions); token counts from upstream response metadata when available
- Prometheus scrape interval 15 s; TSDB retention 30 days (SC-002, Assumptions)
- Monitoring provisioning hooks into existing deployment lifecycle (`running` → provision, `deleted` → decommission schedule)

**Scale/Scope**: Student-project scale — single Prometheus + Grafana instance, ≤ 3 concurrent deployments per user, 30-day active retention, 7-day post-delete operator retention.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Clean & Readable Code | ✅ PASS | New modules follow existing naming (`metrics_store.py`, `prometheus_provisioner.py`, `grafana_provisioner.py`, `metrics_api.py`). No extra abstraction layers beyond provider protocols needed for test injection. |
| II. Security First | ✅ PASS | Grafana links are HMAC-signed, time-limited, scoped to `deployment_id` + `user_id`. Cross-user access rejected. PromQL queries always inject `deployment_id` + `user_id` label matchers server-side — never trusted from client. Signing secret from env var, never logged or returned in API responses. |
| III. Direct Framework & Library Usage | ✅ PASS | `prometheus-client` used directly in inference proxy. Grafana provisioning via Grafana HTTP API (`httpx`). PromQL via Prometheus HTTP API — no wrapper ORM for metrics. |
| IV. TDD Mandatory | ✅ PASS | Contract tests written first for metrics GET, Grafana link GET, ownership denial, empty state, deleted deployment 404, Prometheus-unavailable error. Red → green → refactor per task. |
| V. Realistic & Comprehensive Testing | ✅ PASS | Real SQLite for `deployment_monitoring` rows. Fake provisioners stub only external HTTP boundaries. Integration tests cover running-deployment metrics panel render and error/empty states via AppTest. |
| VI. Simplicity & Root Cause Resolution | ✅ PASS | Reuses deployment orchestrator status transitions for provisioning triggers. Single shared Prometheus with label isolation (not one Prometheus pod per deployment). CPU path adds scrape job for existing TGI `/metrics` — no GKE monitoring stack rebuild. |

**Complexity Tracking** (constitution violations requiring justification):

| Item | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| New `deployment_monitoring` table | Tracks provisioned scrape job + Grafana datasource UIDs and decommission schedule across process restarts | Storing UIDs only in memory loses provisioning state on backend restart; recomputing from deployment row alone cannot recover Grafana datasource UID |
| Background decommission job | FR-014 requires 7-day post-delete retention before purge | Immediate purge on delete violates operator retention requirement; manual ops cleanup is error-prone |
| HMAC signed redirect endpoint | FR-009a requires session-scoped Grafana access without separate login | Direct Grafana URL exposes unauthenticated dashboard; embedding credentials in URL violates Security First |

**Post-design re-check**: ✅ All gates still pass. Contracts limit surface area to two new authenticated endpoints plus one redirect handler validated by signed token.

---

## Project Structure

### Documentation (this feature)

```text
specs/010-prometheus-grafana-monitoring/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── openapi.yaml     ← Phase 1 output
└── checklists/
    └── requirements.md  ← from /speckit-specify + /speckit-clarify
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                                      # MODIFIED: register metrics router; start decommission loop
│   ├── api/
│   │   ├── metrics.py                               # NEW: GET metrics, GET grafana link, GET redirect
│   │   └── deployment.py                            # MODIFIED: pass deployment_id + user_id to metrics_recorder from inference handler
│   ├── models/
│   │   └── metrics.py                               # NEW: DeploymentMetricsResponse, GrafanaLinkResponse
│   ├── db/
│   │   ├── models.py                                # MODIFIED: DeploymentMonitoringRow
│   │   └── migrations.py                            # MODIFIED: additive migration for deployment_monitoring
│   └── services/
│       ├── inference_proxy.py                       # MODIFIED: TTFT timing + token counting hooks
│       ├── metrics_recorder.py                      # NEW: prometheus_client histograms/counters
│       ├── metrics_query.py                         # NEW: PromQL queries → API response shape
│       ├── metrics_store.py                         # NEW: CRUD for deployment_monitoring rows
│       ├── monitoring_orchestrator.py               # NEW: provision/decommission on status transitions
│       ├── prometheus_provisioner.py                # NEW: protocol + real (file-based scrape config reload)
│       ├── prometheus_fake_provisioner.py           # NEW: fake for contract tests
│       ├── grafana_provisioner.py                   # NEW: protocol + real (Grafana HTTP API)
│       ├── grafana_fake_provisioner.py              # NEW: fake for contract tests
│       ├── grafana_signed_url.py                    # NEW: HMAC token mint + validate
│       └── deployment_orchestrator.py               # MODIFIED: call monitoring_orchestrator on running/deleted
├── monitoring/
│   ├── prometheus.yml                               # NEW: base Prometheus config template
│   ├── scrape.d/                                    # NEW: per-deployment scrape job fragments (generated)
│   └── grafana/
│       ├── provisioning/datasources/.gitkeep        # NEW: optional static provisioning
│       └── dashboards/deployment-metrics.json       # NEW: dashboard template (imported per deployment)
├── docker-compose.monitoring.yml                    # NEW: Prometheus + Grafana for local dev
└── tests/contract/
    ├── conftest.py                                  # MODIFIED: fake provisioner fixtures
    ├── test_metrics_api.py                          # NEW: metrics + grafana link contract tests
    └── test_deployment_api.py                       # MODIFIED: inference records metrics samples

frontend/
├── src/
│   ├── components/
│   │   ├── deployment_metrics.py                    # NEW: metrics panel (charts, empty/error, Grafana link)
│   │   └── deployments_list.py                      # MODIFIED: embed metrics panel for running deployments
│   └── services/
│       └── api_client.py                            # MODIFIED: get_deployment_metrics, get_grafana_link
└── tests/integration/
    └── test_workflow.py                             # MODIFIED: metrics panel scenarios
```

**Structure Decision**: Web application (backend + frontend) — consistent with features 006–009. Prometheus/Grafana run as separate containers via docker-compose; backend integrates via HTTP APIs and generated scrape configs.

---

## Phase 0: Research

See [`research.md`](./research.md) — all technical unknowns resolved.

---

## Phase 1: Design

See:
- [`data-model.md`](./data-model.md) — entities, Prometheus metric catalog, lifecycle
- [`contracts/openapi.yaml`](./contracts/openapi.yaml) — metrics API endpoints
- [`quickstart.md`](./quickstart.md) — local dev setup with monitoring stack

---

## Phase 2: Task Breakdown

Deferred to `/speckit-tasks` — not produced by this command.
