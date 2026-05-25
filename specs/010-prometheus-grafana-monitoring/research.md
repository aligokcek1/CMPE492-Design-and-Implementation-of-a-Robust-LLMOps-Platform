# Research: Deployment Metrics Monitoring — Feature 010

**Date**: 2026-05-24 | **Branch**: `010-prometheus-grafana-monitoring`

---

## 1. Per-Deployment Prometheus "Namespace" on a Shared Instance

### Decision
Use a **single platform Prometheus server** with **one dynamically registered scrape job per deployment**, named `deployment-<deployment_id>`. All proxy-emitted metrics carry mandatory labels `{deployment_id, user_id, hardware_type}`. Scraped TGI metrics are relabeled with the same labels via `relabel_configs`.

### Rationale
Running one Prometheus pod per deployment is operationally heavy for a student project and unnecessary when label isolation satisfies FR-004 and FR-009. The spec's "scrape-target namespace" maps cleanly to a dedicated scrape job + label set, not a literal separate Prometheus instance.

### Implementation sketch
- Base config: `backend/monitoring/prometheus.yml` with `scrape_config_files: ['scrape.d/*.yml']`
- On `running`: `prometheus_provisioner.provision(deployment_id, endpoint_url, hardware_type)` writes `scrape.d/<deployment_id>.yml` and POSTs to Prometheus `/-/reload`
- CPU scrape target: `{endpoint_url}/metrics` (TGI exposes Prometheus metrics on the inference port)
- GPU scrape target: `{endpoint_url}/metrics` when LitServe/vLLM exposes it; job still registered but hardware panels may return N/A
- On delete schedule: remove scrape file + reload; optional `metric_relabel_configs` drop rule after retention window

### Alternatives Considered
- **Prometheus per deployment**: full isolation but multiplies ops cost; rejected for student-project scale.
- **Single global scrape with only proxy metrics**: misses TGI-native throughput/latency series and CPU/memory process metrics; rejected.

---

## 2. TTFT and Throughput Instrumentation at the Inference Proxy

### Decision
Add `metrics_recorder.py` using `prometheus-client` directly in the backend process. Instrument `inference_proxy.forward()`:

| Metric | Type | Labels | Notes |
|---|---|---|---|
| `llmops_ttft_seconds` | Histogram | `deployment_id`, `user_id`, `hardware_type` | Time from request start to first response byte |
| `llmops_tokens_total` | Counter | `deployment_id`, `user_id`, `hardware_type` | Increment by token count when available |
| `llmops_inference_requests_total` | Counter | `deployment_id`, `user_id`, `hardware_type`, `outcome` | `success` / `error` / `no_token` |

Expose backend metrics at `GET /metrics` on the FastAPI app (standard `prometheus_client.make_asgi_app()` mount).

### TTFT measurement boundary
- **CPU (TGI `/generate`)**: Non-streaming today — TTFT equals time-to-first-byte of the HTTP response body (acceptable v1 approximation; documented in Assumptions). Failed requests before body bytes → `outcome=no_token`, excluded from TTFT histogram (FR-013).
- **GPU (vLLM `/v1/chat/completions`)**: Same non-streaming measurement in v1. Optional follow-up: enable `stream=true` and record first SSE chunk timestamp for true token-level TTFT.

### Throughput
- Primary: `rate(llmops_tokens_total[5m])` → tokens/s
- Fallback when token count unavailable: `rate(llmops_inference_requests_total{outcome="success"}[5m])` → requests/s; API labels unit accordingly (spec Assumption)

### Rationale
Proxy boundary is consistent across CPU/GPU (spec Assumption). `prometheus-client` is the standard Python approach — no wrapper (constitution III).

### Alternatives Considered
- **Only scrape upstream /metrics**: misses requests that fail before upstream emits metrics; proxy counters capture full request lifecycle.
- **OpenTelemetry**: heavier dependency; Prometheus was explicitly requested.

---

## 3. CPU Hardware Metrics via TGI `/metrics`

### Decision
Scrape the deployment's public LoadBalancer endpoint at `/metrics`. Use these series (when present):

| Panel | PromQL (after relabel) | Fallback |
|---|---|---|
| CPU utilization | `rate(process_cpu_seconds_total{deployment_id="..."}[5m])` | N/A message |
| Memory utilization | `process_resident_memory_bytes{deployment_id="..."}` | N/A message |

TGI also exposes request-level metrics (`tgi_*`) usable for cross-checking throughput; primary user-facing throughput remains proxy token counter.

### Rationale
TGI 3.x exposes Prometheus metrics on the inference port by default — no manifest change required beyond ensuring `/metrics` is reachable on the LoadBalancer service (same port 80 → 8000 mapping).

### Risk
LoadBalancer `/metrics` is publicly reachable on GKE — acceptable for student project; production hardening (NetworkPolicy, internal LB) is out of scope.

---

## 4. GPU Hardware Metrics — Lightning AI Limitations

### Decision
Attempt scrape of `{endpoint_url}/metrics` for LitServe/vLLM process metrics. If GPU utilization series are absent after provisioning grace period (5 min), API returns:

```json
"gpu_utilization": {"available": false, "reason": "not_available_for_this_deployment_type"}
```

TTFT and throughput panels always populated from proxy metrics regardless.

### Rationale
Matches clarified spec (partial with explicit N/A). Lightning AI managed cloud does not guarantee NVIDIA DCGM-style metrics to the platform.

---

## 5. Grafana Per-Deployment Datasource + Signed Deep Links

### Decision
- **Grafana provisioning**: On deployment `running`, call Grafana HTTP API (`POST /api/datasources`) to create datasource:
  - Name: `deployment-<deployment_id>`
  - Type: `prometheus`
  - URL: `http://prometheus:9090` (docker network)
  - UID: `dep-<deployment_id>` (stored in `deployment_monitoring.grafana_datasource_uid`)
- **Dashboard**: Import shared JSON template `deployment-metrics.json` into a per-deployment folder; UID `dash-<deployment_id>`. All panels use the deployment datasource; PromQL includes `{deployment_id="<id>"}`.
- **Signed link flow**:
  1. `GET /api/deployments/{id}/metrics/grafana` (authenticated) → `{redirect_url, expires_at}`
  2. `redirect_url` = `{BACKEND_PUBLIC_URL}/api/metrics/grafana/redirect?token=<hmac>`
  3. Token payload (HMAC-SHA256 with `LLMOPS_GRAFANA_SIGNING_SECRET`): `{deployment_id, user_id, exp}`
  4. Redirect handler validates token + ownership → `302` to `{GRAFANA_PUBLIC_URL}/d/dash-{id}?orgId=1&kiosk`
  5. Default TTL: **15 minutes** (planning default; configurable via `LLMOPS_GRAFANA_LINK_TTL_SECONDS`)

### Rationale
Per-deployment datasource satisfies clarified topology while pointing at one Prometheus backend. Signed redirect through backend enforces session ownership without Grafana login or anonymous access.

### Alternatives Considered
- **Grafana auth proxy**: requires nginx sidecar and callback endpoint — more moving parts.
- **Grafana service account tokens per user**: Grafana user provisioning out of scope.
- **iframe embed**: explicitly rejected in clarifications.

---

## 6. In-Platform Metrics API (Streamlit Data Source)

### Decision
`GET /api/deployments/{deployment_id}/metrics?range=1h|24h|7d` queries Prometheus via HTTP API (`/api/v1/query_range`) server-side. Returns JSON tailored for Streamlit charts — no PromQL exposed to frontend.

Response includes:
- `summary`: avg TTFT, p95 TTFT, avg throughput + unit label
- `series`: time arrays for charts
- `hardware`: per-series `available` flag + `reason` when N/A
- `empty`: true when no inference traffic in range
- `error`: populated when Prometheus unreachable (FR-011)

### Rationale
Hybrid UX (clarified): Streamlit renders native charts from this API; Grafana link is additive.

---

## 7. Lifecycle — Provision, Delete, Decommission

### Decision

| Event | Action |
|---|---|
| Deployment → `running` | `monitoring_orchestrator.provision()` — scrape job + Grafana datasource + dashboard; insert `deployment_monitoring` row |
| Deployment → `deleted` | Immediately remove metrics UI eligibility; `monitoring_orchestrator.schedule_decommission()` sets `decommission_at = now + 7d` |
| Background loop (60 s) | Decommission due rows — remove scrape job, delete Grafana datasource, delete dashboard, purge `deployment_monitoring` row |
| Backend startup | Reconcile: ensure scrape jobs exist for all `running` deployments with monitoring rows |

### Rationale
Matches FR-004a/b, FR-014, FR-014a. Reconciliation handles backend restarts without orphaned or missing scrape configs.

---

## 8. Local Dev Stack

### Decision
Add `docker-compose.monitoring.yml` at repo root:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.55.0
    volumes:
      - ./backend/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./backend/monitoring/scrape.d:/etc/prometheus/scrape.d
    ports: ["9090:9090"]
  grafana:
    image: grafana/grafana:11.3.0
    ports: ["3000:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_AUTH_ANONYMOUS_ENABLED: "false"
```

Backend env vars:

| Variable | Purpose |
|---|---|
| `LLMOPS_PROMETHEUS_URL` | `http://localhost:9090` |
| `LLMOPS_GRAFANA_URL` | `http://localhost:3000` |
| `LLMOPS_GRAFANA_SIGNING_SECRET` | HMAC secret for signed links |
| `LLMOPS_GRAFANA_ADMIN_USER/PASSWORD` | Grafana API provisioning |
| `LLMOPS_METRICS_DISABLED` | `1` skips provisioning in tests |

### Rationale
Realistic testing (constitution V) for manual E2E; contract tests use fakes with `LLMOPS_METRICS_DISABLED=1`.

---

## 9. Contract Test Strategy

### Decision
- `FakePrometheusProvisioner`: records provision/decommission calls; no filesystem writes
- `FakeGrafanaProvisioner`: returns deterministic UIDs
- `FakeMetricsQueryClient`: returns canned PromQL results for TTFT/throughput/hardware scenarios (including GPU N/A)
- Tests cover: happy path metrics, empty state, prometheus unavailable, wrong user 403, deleted deployment 404, grafana link mint + expired token 403

### Rationale
Mirrors `FakeGCPProvider` / `FakeLightningAIProvider` pattern from features 007/008.
