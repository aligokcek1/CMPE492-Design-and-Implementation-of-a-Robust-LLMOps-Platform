# Feature Specification: Deployment Metrics Monitoring with Prometheus and Grafana

**Feature Branch**: `010-prometheus-grafana-monitoring`  
**Created**: 2026-05-24  
**Status**: Draft  
**Input**: User description: "Integrate Prometheus and Grafana to monitor deployed models. Track TTFT (time to first token), hardware usage, and average throughput for CPU (GKE/TGI) and GPU (Lightning AI) deployments."

## Clarifications

### Session 2026-05-24

- Q: How should in-app metrics be presented relative to Grafana? → A: Hybrid — summary stats and trend charts in the platform Deployments UI; "Open in Grafana" link for advanced drill-down.
- Q: What monitoring stack topology should be used? → A: Per-deployment stack — each running deployment gets its own Prometheus scrape-target namespace; shared Grafana with per-deployment datasources.
- Q: How should users authenticate to Grafana? → A: Signed deep links — platform generates time-limited, deployment-scoped Grafana URLs from the active session; no separate Grafana login.
- Q: How should GPU hardware metrics behave when Lightning AI exposes limited data? → A: Partial with explicit N/A — TTFT and throughput always shown; unavailable GPU/memory series labeled "not available for this deployment type".
- Q: Can users view metrics after a deployment is deleted? → A: No post-delete UI access — metrics disappear from the platform immediately on delete; 7-day retention is backend-only for platform operators.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Performance Metrics for a Running Deployment (Priority: P1)

A logged-in user with at least one deployment in the **running** state opens that deployment's metrics view from the Deployments section. They see current summary values for **time to first token (TTFT)** and **average throughput**. Summary stats are rendered **in the platform UI** (not via embedded Grafana frames). **Hardware utilization charts are delivered in User Story 3 (P3)**; the US1 MVP focuses on inference performance (TTFT + throughput) plus empty/error states.

**Why this priority**: TTFT and throughput are the minimum signals needed to confirm a deployment is serving inference. Operators can validate basic health before hardware differentiation (P3) and trend analysis (P2).

**Independent Test**: Can be fully tested by deploying a model, sending one or more inference requests, and verifying that TTFT and throughput appear in the deployment's metrics view within the expected freshness window (or an explicit empty state before the first request).

**Acceptance Scenarios**:

1. **Given** a logged-in user with a **running** CPU or GPU deployment, **When** they open the metrics view after at least one inference request, **Then** they see TTFT and average throughput summary values with clearly labeled units.
2. **Given** a logged-in user with a **running** GPU deployment on Lightning AI, **When** they open the metrics view after at least one inference request, **Then** they see TTFT and average throughput (hardware utilization is covered by User Story 3).
3. **Given** a deployment that has reached **running** but has received no inference traffic yet, **When** the user opens the metrics view, **Then** they see an empty-state message explaining that metrics will appear after the first inference request.
4. **Given** a deployment in **deploying**, **failed**, or **deleted** state, **When** the user views it in the Deployments list, **Then** the metrics view is unavailable — deleted deployments show no historical metrics in the platform UI. (**Open in Grafana** unavailability for non-running states is enforced once User Story 4 is delivered.)

---

### User Story 2 — Track TTFT and Throughput Trends Over Time (Priority: P2)

A user investigating model performance opens a deployment's metrics view and reviews TTFT and throughput over selectable time ranges (e.g., last hour, last 24 hours, last 7 days). They can see average values and distribution indicators (such as typical range or percentile bands) to understand latency and serving capacity under load.

**Why this priority**: Point-in-time snapshots help confirm a deployment works; trends reveal degradation, cold-start effects, and capacity limits — essential for operating models in production.

**Independent Test**: Can be fully tested by generating inference traffic over a known period and verifying that TTFT and throughput charts reflect the activity pattern for the selected time range.

**Acceptance Scenarios**:

1. **Given** a **running** deployment with inference traffic over the past 24 hours, **When** the user selects the "last 24 hours" time range, **Then** TTFT and average throughput charts display data points covering that window with clearly labeled axes and units.
2. **Given** a deployment with bursty traffic, **When** the user views throughput over time, **Then** they can identify periods of higher and lower serving rate without needing to inspect raw logs.
3. **Given** a deployment where some inference requests fail before producing a token, **When** the user views TTFT aggregates, **Then** only requests that produced at least one token contribute to TTFT statistics, and the view indicates if failed requests are excluded from TTFT.

---

### User Story 3 — Compare Hardware Utilization by Deployment Type (Priority: P3)

A user operating both CPU and GPU deployments opens metrics for each and can understand how hardware resources are being consumed. CPU deployments show processor and memory pressure; GPU deployments show accelerator and memory pressure. Terminology and chart labels match the underlying platform (GKE/TGI for CPU, Lightning AI for GPU) so the user knows which cloud path they are observing.

**Why this priority**: Hardware usage drives cost and capacity decisions. Distinct CPU vs GPU presentations prevent misinterpretation when users run mixed workloads.

**Independent Test**: Can be fully tested by running one CPU and one GPU deployment concurrently, opening each metrics view, and confirming that resource charts show the correct resource types and platform labels for each hardware path.

**Acceptance Scenarios**:

1. **Given** a **running** CPU deployment, **When** the user views hardware utilization, **Then** charts show CPU and memory usage (not GPU metrics) with labels referencing the CPU/GKE deployment path.
2. **Given** a **running** GPU deployment, **When** the user views hardware utilization, **Then** charts show GPU and memory usage (not CPU-only metrics) with labels referencing the GPU/Lightning AI deployment path.
3. **Given** a user with multiple deployments, **When** they open metrics for deployment A, **Then** they see only metrics scoped to deployment A — not aggregated or mixed with other deployments.

---

### User Story 4 — Access Grafana Dashboards from the Platform (Priority: P4)

A user who needs deeper analysis follows an **"Open in Grafana"** link from the in-platform metrics view to a pre-built Grafana dashboard filtered to that deployment. The in-platform view (P1–P3) covers summary stats and trend charts for everyday monitoring; Grafana provides advanced drill-down (custom time ranges, percentile bands, correlated series) for power users. Both surfaces show the same core metrics (TTFT, throughput, hardware usage) scoped to the same deployment.

**Why this priority**: The hybrid model keeps routine monitoring inside the platform while Grafana serves advanced analysis without requiring every user to leave the app for basic visibility.

**Independent Test**: Can be fully tested by clicking the Grafana link from a deployment's metrics view and verifying the opened dashboard is scoped to that deployment and shows TTFT, throughput, and hardware charts.

**Acceptance Scenarios**:

1. **Given** a **running** deployment with collected metrics, **When** the user clicks "Open in Grafana" (or equivalent) from the metrics view, **Then** the platform generates a time-limited signed URL scoped to that deployment's Grafana datasource and dashboard, and the user lands on the pre-filtered view without a separate Grafana login.
2. **Given** a user who is not authorized to view another user's deployment, **When** they attempt to open a Grafana dashboard URL for that deployment (including expired or tampered signed links), **Then** access is denied — metrics remain isolated per user/deployment.
3. **Given** a signed Grafana link that has expired, **When** the user attempts to open it, **Then** access is denied and the user is directed to regenerate the link from the platform metrics view.

---

### Edge Cases

- What happens when a deployment transitions from **deploying** to **running**? Metrics collection begins at **running**; the platform provisions a dedicated Prometheus scrape-target namespace and a matching Grafana datasource for that deployment before surfacing live metrics.
- What happens when a deployment is **deleted**? Metrics collection stops immediately; the in-platform metrics view and **"Open in Grafana"** link are removed from the UI with no post-delete historical access for users. Raw metric data is retained in the backend for at least 7 days (FR-014) for platform-operator use only, then the scrape-target namespace and Grafana datasource are decommissioned and data is purged.
- What if Prometheus or Grafana is temporarily unavailable? The platform shows a clear error in the metrics view and does not display misleading zero values as if the deployment were idle.
- What if Lightning AI exposes limited hardware metrics compared to GKE? GPU deployments MUST always show TTFT and throughput; GPU and memory series are shown when the provider exposes them. Unavailable series display **"not available for this deployment type"** — the platform MUST NOT infer, estimate, or proxy synthetic GPU utilization values.
- What if inference traffic is extremely low (one request per hour)? Aggregates still update; charts may show sparse data with appropriate time-range guidance.
- What if TTFT cannot be measured for a streaming response? TTFT is recorded at the moment the first token (or first content chunk treated as a token) is received.
- What if a signed Grafana link expires while the user is viewing a dashboard? The session ends at link expiry; the user must return to the platform metrics view and click **"Open in Grafana"** again to obtain a fresh signed URL.
- What if the user exceeds concurrent deployment limits? Monitoring does not apply to deployments that were never created; existing running deployments remain monitorable.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The platform MUST collect **time to first token (TTFT)** for inference requests against **running** deployments on both CPU (GKE/TGI) and GPU (Lightning AI) paths.
- **FR-002**: The platform MUST compute and expose **average throughput** (tokens served per unit time) per deployment, aggregated over configurable time windows.
- **FR-003**: The platform MUST collect **hardware utilization** metrics appropriate to deployment type: CPU and memory for CPU deployments; GPU and memory for GPU deployments when exposed by the provider.
- **FR-003a**: For GPU deployments where Lightning AI does not expose a hardware series, the platform MUST still show TTFT and throughput and MUST label the missing GPU/memory series **"not available for this deployment type"** rather than inferring, estimating, or hiding the entire hardware section.
- **FR-004**: Metrics MUST be stored in **Prometheus** and visualized through **Grafana**. Each **running** deployment MUST have its own dedicated Prometheus scrape-target namespace; a **shared Grafana instance** MUST expose a per-deployment datasource bound to that namespace.
- **FR-004a**: When a deployment reaches **running**, the platform MUST provision the deployment's scrape-target namespace and Grafana datasource before metrics are offered in the UI.
- **FR-004b**: When a deployment is **deleted**, the platform MUST decommission its scrape-target namespace and Grafana datasource after the retention period defined in FR-014.
- **FR-005**: Users MUST be able to open a deployment-specific metrics view from the Deployments section for any **running** deployment they own; metrics views MUST NOT be offered for **deleted** deployments.
- **FR-005a**: The in-platform metrics view MUST render summary stats and trend charts natively in the Deployments UI (not via embedded Grafana iframes); Grafana is accessed only via an explicit **"Open in Grafana"** link for advanced drill-down.
- **FR-006**: The metrics view MUST display TTFT, average throughput, and hardware utilization with units and labels understandable to non-expert operators.
- **FR-007**: CPU and GPU deployments MUST use visually and semantically distinct presentations so users can tell which hardware path and platform they are viewing.
- **FR-008**: Metrics collection MUST begin when a deployment reaches **running** status and MUST stop updating when the deployment reaches **deleted** status.
- **FR-009**: Users MUST only see metrics for deployments they own; cross-user metric access MUST NOT be possible via the platform UI or linked Grafana dashboards.
- **FR-009a**: **"Open in Grafana"** links MUST be time-limited signed URLs generated from the user's active platform session, scoped to that deployment's Grafana datasource; users MUST NOT require a separate Grafana login.
- **FR-009b**: Expired, tampered, or unauthorized signed Grafana URLs MUST be rejected without exposing metrics from other deployments.
- **FR-010**: When no inference traffic has occurred, the metrics view MUST show an explicit empty state rather than implying zero performance.
- **FR-011**: When the monitoring backend is unreachable, the platform MUST surface a user-visible error state instead of silent failure or fabricated values.
- **FR-012**: Users MUST be able to navigate to a **Grafana** dashboard pre-scoped to a specific **running** deployment from the deployment metrics view via a platform-generated signed deep link; signed Grafana links MUST NOT be generated for **deleted** deployments.
- **FR-013**: TTFT aggregates MUST include only requests that successfully produced at least one output token; failed or cancelled requests MUST NOT skew TTFT averages without indication.
- **FR-014**: After a deployment is **deleted**, raw metric data MUST be retained in the backend for at least 7 days before purge for platform-operator use; users MUST NOT have access to this retained data via the platform UI or Grafana links.
- **FR-014a**: Upon deletion, the platform MUST immediately remove the metrics view and **"Open in Grafana"** entry point from the Deployments UI — no grace-period read-only access for users.

### Key Entities

- **Deployment Metric Series**: Time-stamped measurements tied to a single deployment, including TTFT samples, throughput rollups, and hardware utilization readings; stored within that deployment's dedicated Prometheus scrape-target namespace; distinguished by hardware type (CPU vs GPU).
- **Metric Aggregate**: A computed summary over a time window (e.g., average TTFT over the last hour, average tokens per second over the last 24 hours) derived from raw series data.
- **Monitoring View**: The in-platform presentation of metrics for one deployment, including native summary stats, trend charts, empty/error states, and an **"Open in Grafana"** link for advanced analysis (hybrid model — not iframe-embedded Grafana panels).
- **Dashboard Binding**: Association between a deployment identifier and a Grafana dashboard template with pre-applied filters, routed through that deployment's dedicated Grafana datasource, so users land on the correct scoped view.
- **Deployment Monitoring Namespace**: The isolated Prometheus scrape-target namespace and paired Grafana datasource provisioned for one deployment at **running** and decommissioned after deletion retention.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can access deployment-specific TTFT, throughput, and hardware utilization from the Deployments section in **3 or fewer** navigational steps.
- **SC-002**: Under normal operation, metrics views reflect inference and hardware activity from the **last 60 seconds** within **2 minutes** of that activity occurring.
- **SC-003**: At least **95%** of completed inference requests that produce at least one token are represented in TTFT and throughput aggregates shown to the user.
- **SC-004**: Users operating both CPU and GPU deployments can correctly identify which hardware metrics belong to which deployment type in **90%** of moderated usability sessions (or equivalent structured acceptance test scenarios).
- **SC-005**: When Prometheus or Grafana is unavailable, **100%** of metrics view attempts show an explicit error message rather than blank or misleading zero-value charts.
- **SC-006**: Historical TTFT and throughput trends for the last 7 days are viewable in the platform for any deployment that is currently **running** and received traffic during that period.

---

## Assumptions

- **Prometheus** is the metrics storage and query backend; **Grafana** is the visualization layer. This matches the explicit user request and is treated as a product constraint, not an open design choice.
- **Per-deployment monitoring topology**: each running deployment receives its own Prometheus scrape-target namespace; Grafana is a shared platform instance with one datasource per deployment (not a single global datasource filtered by labels).
- Metrics are scraped or pushed from inference runtimes (TGI on GKE for CPU, LitServe/vLLM on Lightning AI for GPU) using each runtime's standard observability hooks where available.
- **GPU hardware fallback**: TTFT and throughput are mandatory for all GPU deployments; GPU/memory utilization is shown only when the provider exposes it — otherwise labeled N/A (no proxy-inferred hardware metrics).
- **Hybrid UX model**: routine monitoring (summary stats + trend charts) lives in the platform Deployments UI; Grafana is linked for advanced drill-down only — not embedded via iframes in v1.
- Users reach Grafana via **time-limited signed deep links** generated from the active platform session (no separate Grafana login); full Grafana administration is out of scope — the platform provides pre-provisioned dashboards only.
- Default metric retention while a deployment is active: **30 days** of user-accessible history in the platform UI. After deletion: metrics are **immediately unavailable** to users; raw data is retained **7 days** in the backend for platform-operator use only (FR-014), then purged.
- Throughput is expressed as **tokens per second** averaged over the selected window; if token counts are unavailable for a given request, the platform falls back to **requests per second** and labels the chart accordingly.
- **TTFT v1 measurement**: TTFT is measured at the inference proxy boundary. For non-streaming CPU (TGI `/generate`) and GPU (vLLM `/v1/chat/completions`) paths in v1, TTFT equals **time to first response byte** (HTTP body start) as a practical proxy for first-token latency. True per-token streaming TTFT (first SSE chunk) is a follow-up enhancement when streaming inference is enabled.
- Monitoring is available only while a deployment is **running**; there is no post-delete metrics access for users in the platform UI or via Grafana signed links.
- Multi-tenant isolation follows the same ownership rules as the existing Deployments list — one user's metrics never appear in another user's views.
- Alerting (PagerDuty, email alerts, SLO burn rates) is **out of scope** for this feature; users observe metrics manually via the platform and Grafana.
- Cost of Prometheus/Grafana infrastructure is borne by the platform operator; end users are not billed separately for metrics storage in v1.
