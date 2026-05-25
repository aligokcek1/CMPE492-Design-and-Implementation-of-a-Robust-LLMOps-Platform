# UI Layout Contract: Production-Grade Operations Dashboard — Feature 011

**Date**: 2026-05-25 | **Branch**: `011-streamlit-dashboard-refactor`  
**Scope**: Streamlit client presentation only — no REST API changes.

---

## Authenticated shell

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR                          │ MAIN (layout=wide)                        │
│ ─────────────────                │                                           │
│ LLMOps Platform (no emoji)       │ [optional credential warning banner]      │
│ Signed in as {username}          │                                           │
│ [Sign Out]                       │ st.tabs (default = first tab):            │
│ ─────────────────                │ ┌──────────────────────────────────────┐  │
│ ▼ Settings (expander)            │ │ Deployments │ Upload │ Select │ Deploy│ │
│    ├─ GCP Credentials (form)     │ └──────────────────────────────────────┘  │
│    └─ Lightning AI (form)        │ {active tab content}                      │
│ ─────────────────                │                                           │
│ caption: course attribution      │                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployments tab

```
┌─ Fleet overview (st.columns 3 × st.metric) ─────────────────────────────────┐
│  Active          Provisioning        Failed                                  │
│  {n_running}     {n_queued+...}      {n_failed+lost}                         │
└──────────────────────────────────────────────────────────────────────────────┘

[ ] Show terminated

For each visible deployment:
┌─ Row (st.columns [4,2,4]) ──────────────────────────────────────────────────┐
│ METADATA              │ STATUS (badge)  │ ENDPOINT + ACTIONS                 │
│ Title                 │ Queued          │ Pending | st.code(url) + Copy      │
│ `repo_id`             │                 │ [Delete] or [Dismiss]              │
│ CPU · GKE | GPU · …   │                 │                                    │
│ [Uploaded]            │                 │                                    │
└──────────────────────────────────────────────────────────────────────────────┘
▼ Details (st.expander, collapsed)
    ├─ status_message (if any)
    ├─ metrics panel (running)
    ├─ inference form (running + endpoint)
    └─ errors (inline st.error)

Deleted rows: hidden unless Show terminated; shown de-emphasized; excluded from metrics.
```

---

## Tab labels (exact strings)

| # | Label |
|---|-------|
| 1 | `Deployments` |
| 2 | `Upload Model` |
| 3 | `Select Model` |
| 4 | `Deploy` |

**Forbidden** in chrome: emoji prefixes, legacy names `☁️ GCP Credentials`, `⚡ Lightning AI`, `📤 Upload Model`, etc.

---

## Fleet count contract

| Metric label | Includes `status` |
|--------------|-------------------|
| Active | `running` |
| Provisioning | `queued`, `deploying`, `deleting` |
| Failed | `failed`, `lost` |

`deleted` → never counted. List filter excludes `deleted` when `show_terminated` is false.

---

## Row action contract

| Condition | Collapsed row actions | Disclosure |
|-----------|----------------------|------------|
| `running` | Copy, Delete | Metrics, Inference, Grafana |
| `failed` | Copy (if URL), Delete | status_message, errors |
| `lost` | Dismiss | status_message |
| `deleting` | Delete disabled | status_message |
| `deleted` (visible) | Copy disabled, Delete disabled | minimal read-only |

---

## Credential warning banner

When GCP or Lightning invalid:

- Text references **Settings → GCP Credentials** or **Settings → Lightning AI**
- No emoji tab names

---

## Unauthenticated

Main area: login only. Sidebar: not authenticated info (existing pattern).
