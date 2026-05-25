# Quickstart: Production-Grade Operations Dashboard UI — Feature 011

**Branch**: `011-streamlit-dashboard-refactor`

---

## Prerequisites

Existing backend + session from features 006–010. No new environment variables.

```bash
# Terminal 1 — backend
cd backend && uvicorn src.main:app --reload

# Terminal 2 — frontend
cd frontend && streamlit run src/app.py
```

---

## Verify navigation (US5)

1. Sign in with a valid HF token.
2. Confirm **four tabs** in order: **Deployments**, **Upload Model**, **Select Model**, **Deploy**.
3. Confirm **Deployments** is selected on first load (first tab).
4. Confirm sidebar shows username + **Sign Out** without opening Settings.
5. Expand **Settings** — GCP and Lightning AI forms appear (no main-area credential tabs).

### Narrow viewport (US3)

1. Resize browser to **1280px** width (or use devtools responsive mode).
2. Open sidebar **Settings** expander — GCP and Lightning AI forms remain usable without horizontal clipping of primary controls.

### Invalid credentials banner (FR-008)

1. Configure invalid GCP credentials in **Settings**.
2. Open **Deploy** tab and attempt a CPU deploy — main workspace shows a warning referencing **Settings → GCP Credentials** (not a removed tab name).

---

## Verify fleet overview (US1)

1. Open **Deployments** with mixed statuses (or mock via API).
2. Confirm three metrics: **Active**, **Provisioning**, **Failed**.
3. Toggle a deployment from deploying → running; counts update on rerun/refresh.
4. With only deleted deployments, enable **Show terminated** to see rows; overview stays 0/0/0.

---

## Verify deployment rows (US2)

1. Collapsed row shows three zones; **no emoji** status icons.
2. Running deployment: `st.code` endpoint with one-click copy; **Delete** only in row.
3. Expand **Details**: metrics, inference, Grafana link present; not in collapsed row.
4. Uploaded model shows text label **Uploaded** (not emoji badge).

---

## Verify sidebar credentials (US3)

1. Save GCP credentials from **Settings** expander.
2. Invalidate credentials — banner on main area points to **Settings → GCP Credentials**.

---

## Run tests

```bash
cd frontend && pytest tests/integration/test_workflow.py -q
cd frontend && pytest tests/unit/test_fleet_counts.py -q   # after implementation
cd frontend && ruff check .
```

**SC-005**: All existing integration tests must pass after updating tab/badge assertions.

---

## Acceptance screenshot (SC-006)

1. Capture before/after screenshots at 1920×1080 with 10 deployments, all disclosures collapsed.
2. Compare vertical pixels: fleet overview + 10 rows ≥ 30% shorter than bordered-card baseline.
