# Data Model: Production-Grade Operations Dashboard UI — Feature 011

**Date**: 2026-05-25 | **Branch**: `011-streamlit-dashboard-refactor`

Presentation-layer model only — **no new backend tables or API fields** (FR-013). All entities are derived from existing deployment API JSON and Streamlit `session_state`.

---

## 1. API inputs (unchanged)

Consumed from `GET /api/deployments` via `list_deployments()` — each item:

| Field | Type | UI use |
|-------|------|--------|
| `id` | string | Row keys, delete/dismiss actions |
| `status` | string | Status column, fleet bucketing, row actions |
| `hf_model_id` | string | Metadata caption |
| `hf_model_display_name` | string \| null | Metadata title |
| `hardware_type` | `"cpu"` \| `"gpu"` | Metadata provider label |
| `model_origin` | `"uploaded"` \| `"public"` | Text badge **Uploaded** |
| `endpoint_url` | string \| null | Column three copy block |
| `status_message` | string \| null | Detail disclosure only |

---

## 2. FleetCounts (computed)

```python
@dataclass(frozen=True)
class FleetCounts:
    active: int       # status == "running"
    provisioning: int  # status in ("queued", "deploying", "deleting")
    failed: int       # status in ("failed", "lost")
```

```python
def filter_visible_deployments(
    deployments: list[dict],
    *,
    show_terminated: bool,
) -> list[dict]:
    """When show_terminated is False, exclude status == 'deleted'."""
```

**Rules** (FR-003):
- **deleted** never increments any bucket.
- **Always** call `filter_visible_deployments` before `compute_fleet_counts` and before rendering rows so overview and list stay consistent.

---

## 3. DeploymentRowView (presentation)

| Attribute | Source | Collapsed row | Disclosure |
|-----------|--------|---------------|------------|
| `title` | `hf_model_display_name` or `hf_model_id` | ✓ col 1 | |
| `repo_id` | `hf_model_id` | ✓ caption | |
| `hardware_label` | map(`hardware_type`) → `"CPU · GKE"` / `"GPU · Lightning AI"` | ✓ caption | |
| `origin_label` | `"Uploaded"` if `model_origin == "uploaded"` | ✓ col 1 | |
| `status_label` | map(`status`) | ✓ col 2 badge | |
| `endpoint` | `endpoint_url` | ✓ col 3 `st.code` or `"Pending"` | |
| `primary_action` | `Delete` \| `Dismiss` \| none | ✓ col 3 | |
| `status_message` | `status_message` | | ✓ |
| `metrics_panel` | running only | | ✓ |
| `inference_panel` | running + endpoint | | ✓ |
| `grafana_link` | running only | | ✓ |

---

## 4. Session state keys

| Key | Type | Purpose |
|-----|------|---------|
| `show_terminated` | bool | FR-014 list filter (default `False`) |
| `_confirm_delete_{id}` | bool | Existing delete confirmation |
| `session_token`, `hf_username` | existing | Auth + sidebar profile |

No persistence beyond Streamlit session.

---

## 5. Status → fleet bucket mapping

| `status` | Fleet bucket | In default list |
|----------|--------------|-----------------|
| `running` | active | ✓ |
| `queued`, `deploying`, `deleting` | provisioning | ✓ |
| `failed`, `lost` | failed | ✓ |
| `deleted` | (none) | ✗ unless `show_terminated` |
| dismissed | removed | ✗ |

---

## 6. Status → badge color (implementation)

| `status` | Badge color (Streamlit) |
|----------|------------------------|
| `running` | green |
| `queued`, `deploying`, `deleting` | orange |
| `failed`, `lost` | red |
| `deleted` | gray |

Exact API per `st.badge` docs; labels are plain text (Queued, Deploying, etc.).

---

## 7. Navigation model

| Tab order | Label | Content renderer |
|-----------|-------|------------------|
| 1 (default) | Deployments | `render_deployments_list` + fleet overview |
| 2 | Upload Model | `render_upload_section` |
| 3 | Select Model | `render_model_selector` |
| 4 | Deploy | `render_public_repo_deploy_section` |

Sidebar: profile strip + Settings expander (GCP, Lightning AI).
