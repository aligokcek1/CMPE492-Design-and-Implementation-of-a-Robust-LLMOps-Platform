# Data Model: Deployment Metrics Monitoring — Feature 010

**Date**: 2026-05-24 | **Branch**: `010-prometheus-grafana-monitoring`

---

## 1. New Table: `deployment_monitoring`

Tracks provisioned monitoring resources for each deployment. One row per deployment (created at `running`, removed after decommission).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `deployment_id` | TEXT | PK, FK → `deployments.id` | Deployment being monitored |
| `user_id` | TEXT | NOT NULL, INDEX | Owner (denormalized for query efficiency) |
| `prometheus_scrape_job` | TEXT | NOT NULL | Scrape job name, e.g. `deployment-<uuid>` |
| `grafana_datasource_uid` | TEXT | NOT NULL | Grafana datasource UID, e.g. `dep-<uuid>` |
| `grafana_dashboard_uid` | TEXT | NOT NULL | Grafana dashboard UID, e.g. `dash-<uuid>` |
| `status` | TEXT | NOT NULL, CHECK IN (`active`,`decommissioning`) | Provisioning lifecycle |
| `provisioned_at` | DATETIME | NOT NULL | When monitoring was provisioned |
| `decommission_at` | DATETIME | nullable | Scheduled purge time (set on delete = now + 7d) |
| `created_at` | DATETIME | NOT NULL | Row creation |
| `updated_at` | DATETIME | NOT NULL | Last update |

**SQLAlchemy model**: `DeploymentMonitoringRow` in `backend/src/db/models.py`

**Invariants**:
- Row exists only while deployment is `running` OR in post-delete retention (`decommissioning`)
- No row for `deploying`, `failed`, `queued` deployments
- `user_id` must match parent `deployments.user_id` (enforced in service layer)

---

## 2. Prometheus Metric Catalog

All proxy metrics exposed at backend `GET /metrics`:

| Metric | Type | Labels | Description |
|---|---|---|---|
| `llmops_ttft_seconds` | Histogram | `deployment_id`, `user_id`, `hardware_type` | Time to first response byte |
| `llmops_tokens_total` | Counter | `deployment_id`, `user_id`, `hardware_type` | Total output tokens counted |
| `llmops_inference_requests_total` | Counter | `deployment_id`, `user_id`, `hardware_type`, `outcome` | Request outcomes |

Scraped upstream metrics (CPU, when available) relabeled with `deployment_id`, `user_id`, `hardware_type`:

| Upstream series | Panel |
|---|---|
| `process_cpu_seconds_total` | CPU utilization |
| `process_resident_memory_bytes` | Memory utilization |
| `tgi_request_count` / token counters | Cross-check only |

GPU upstream GPU series (when present): `gpu_utilization` or DCGM equivalents — otherwise API returns N/A.

---

## 3. API Response Models (Pydantic)

### `MetricsRange` (enum)
`1h` | `24h` | `7d`

### `HardwareSeries`
```python
class HardwareSeries(BaseModel):
    available: bool
    reason: str | None = None          # e.g. "not_available_for_this_deployment_type"
    series: list[MetricPoint] = []     # [{timestamp, value}, ...]
```

### `MetricPoint`
```python
class MetricPoint(BaseModel):
    timestamp: datetime
    value: float
```

### `MetricsSummary`
```python
class MetricsSummary(BaseModel):
    ttft_avg_seconds: float | None
    ttft_p95_seconds: float | None
    throughput_value: float | None
    throughput_unit: Literal["tokens_per_second", "requests_per_second"]
    failed_requests_excluded: bool = True
```

### `DeploymentMetricsResponse`
```python
class DeploymentMetricsResponse(BaseModel):
    deployment_id: str
    hardware_type: Literal["cpu", "gpu"]
    platform_label: str                # "GKE / TGI" or "Lightning AI / GPU"
    range: MetricsRange
    summary: MetricsSummary
    series: MetricsSeriesBundle
    empty: bool                        # True when no inference in range
    error: str | None                  # Set when Prometheus unreachable
```

### `GrafanaLinkResponse`
```python
class GrafanaLinkResponse(BaseModel):
    redirect_url: str                  # Backend signed redirect (not raw Grafana URL)
    expires_at: datetime
```

---

## 4. State Transitions

### Deployment × Monitoring lifecycle

```
[no monitoring row]
    │ deployment status → running
    ▼
[deployment_monitoring.status = active]
    │ scrape job + Grafana DS + dashboard live
    │ user sees metrics in UI + can open Grafana
    │
    │ deployment status → deleted
    ▼
[UI: metrics removed immediately]
[deployment_monitoring.status = decommissioning]
[decommission_at = deleted_at + 7 days]
    │ background job when now >= decommission_at
    ▼
[scrape job removed, Grafana DS deleted, row deleted]
[Prometheus retention handles time-series purge per server config]
```

### UI eligibility (derived, not stored)

| Deployment status | Metrics panel | Grafana link |
|---|---|---|
| `running` + active monitoring row | ✅ | ✅ |
| `deploying`, `failed`, `queued` | ❌ | ❌ |
| `deleted`, `deleting` | ❌ | ❌ |
| `lost` | ❌ | ❌ |

---

## 5. Service Layer

### `MetricsStore`
```python
class MetricsStore:
    def create_active(self, *, deployment_id, user_id, scrape_job, ds_uid, dash_uid) -> DeploymentMonitoringRow
    def get_for_deployment(self, deployment_id: str) -> DeploymentMonitoringRow | None
    def mark_decommissioning(self, *, deployment_id: str, decommission_at: datetime) -> None
    def list_due_for_decommission(self, *, now: datetime) -> list[DeploymentMonitoringRow]
    def delete(self, deployment_id: str) -> None
```

### `MonitoringOrchestrator`
```python
class MonitoringOrchestrator:
    async def provision_for_running_deployment(self, row: DeploymentRow) -> None
    async def schedule_decommission(self, deployment_id: str) -> None
    async def run_decommission_cycle(self) -> None
    async def reconcile_on_startup(self) -> None
```

Called from:
- `deployment_orchestrator` when status flips to `running` (after endpoint URL known)
- `deployment_orchestrator` / delete handler when status flips to `deleted`
- `main.py` startup + 60 s background loop

### `MetricsQueryService`
```python
class MetricsQueryService:
    async def fetch_deployment_metrics(
        self, *, deployment_id: str, user_id: str, hardware_type: str, range: MetricsRange
    ) -> DeploymentMetricsResponse
```

Always injects label matchers `{deployment_id="...", user_id="..."}` into PromQL — never accepts raw PromQL from clients.

### `GrafanaSignedUrlService`
```python
class GrafanaSignedUrlService:
    def mint(self, *, deployment_id: str, user_id: str) -> GrafanaLinkResponse
    def validate(self, token: str) -> tuple[str, str]  # deployment_id, user_id
```

---

## 6. Modified Entities

### `DeploymentRow` (read-only relationship)
No schema change. Monitoring eligibility derived from `status` + join to `deployment_monitoring`.

### `inference_proxy.forward()` (behavior change)
After successful inference with ≥1 token:
- Observe `llmops_ttft_seconds`
- Increment `llmops_tokens_total` by counted tokens
- Increment `llmops_inference_requests_total{outcome="success"}`

On error / no token:
- Increment `llmops_inference_requests_total{outcome="error"|"no_token"}`
- Do not observe TTFT histogram

---

## 7. Validation Rules

| Rule | Enforcement |
|---|---|
| Metrics API only for deployment owner | `require_session` + `deployment.user_id == session.username` |
| Metrics API only for `running` deployments | 404 if status != `running` |
| Grafana link only for `running` + active monitoring | 404 otherwise |
| Signed token TTL ≤ 15 min default | `GrafanaSignedUrlService.mint()` |
| Expired/tampered token | 403 on redirect |
| PromQL scoped by deployment + user labels | `MetricsQueryService` — server-side only |
| GPU hardware N/A when series missing | `available=false`, reason string per FR-003a |

---

## 8. Retention

| Data | Retention | User access |
|---|---|---|
| Prometheus time-series (active deployment) | 30 days (Prometheus `--storage.tsdb.retention.time=30d`) | Via platform UI + Grafana |
| Prometheus time-series (post-delete) | Until decommission job runs (≥ 7 days after delete) | Operator only |
| `deployment_monitoring` row | Until decommission completes | N/A |
| Grafana datasource/dashboard | Until decommission | Via signed link while `running` only |
