# Research: Production-Grade Operations Dashboard UI — Feature 011

**Date**: 2026-05-25 | **Branch**: `011-streamlit-dashboard-refactor`

---

## 1. Streamlit layout primitives for wide-screen density

**Decision**: Use `st.set_page_config(layout="wide")` (existing), `st.columns` with ratio `[4, 2, 4]` for deployment rows, `st.metric` × 3 for fleet overview, and borderless `st.container` rows (drop heavy `border=True` cards).

**Rationale**: Spec FR-001/SC-006 require horizontal density and ≥30% vertical reduction. Native columns + metrics match constitution III (direct framework usage) without custom CSS frameworks.

**Alternatives considered**:
- Custom HTML/CSS grid via `st.markdown(unsafe_allow_html=True)` — rejected; harder to test, violates “native components” spirit.
- `st.dataframe` for deployment list — rejected; poor support for per-row actions, disclosures, and copy controls.

---

## 2. Default tab = Deployments

**Decision**: Declare **Deployments** as the first argument to `st.tabs([...])` so Streamlit selects it on load (Streamlit has no separate `default_tab` API).

**Rationale**: FR-007 requires Deployments as default landing tab; first tab is the framework’s default selection behavior.

**Alternatives considered**:
- `st.navigation` pages API — rejected for this refactor; larger IA change than spec requires.
- Session-state tab index hacks — rejected; fragile across Streamlit versions.

---

## 3. Status color without emoji

**Decision**: Replace `_STATUS_BADGES` emoji map with `st.badge(label, color=...)` (Streamlit ≥1.33) or text label + `st.markdown` colored span using a small in-repo `STATUS_STYLES` dict keyed by deployment status.

**Rationale**: FR-010 forbids emoji status icons. `st.badge` is native, accessible, and compact in column two.

**Alternatives considered**:
- Unicode circles (🟢🔴) — rejected by FR-010.
- `st.status` widget — rejected; too tall for dense rows.

---

## 4. One-click endpoint copy

**Decision**: Use `st.code(endpoint_url, language=None)` in column three; Streamlit renders a built-in copy-to-clipboard control on code blocks (1.30+).

**Rationale**: Satisfies SC-004 without `pyperclip` or custom JS.

**Alternatives considered**:
- `st.text_input(..., disabled=True)` + manual copy button — rejected; two clicks.
- Third-party clipboard component — rejected by FR-009.

---

## 5. Row vs disclosure action split

**Decision**: Collapsed row: `st.code` + `st.button("Delete")` / `st.button("Dismiss")`. Detail disclosure: single `st.expander("Details", expanded=False)` wrapping `render_deployment_metrics_panel`, inference form, status_message, and errors.

**Rationale**: Clarification session 2026-05-25 option A; keeps collapsed row height minimal (FR-011).

**Alternatives considered**:
- Metrics button in row — rejected per clarification.
- Nested expanders per concern — rejected; adds vertical noise inside disclosure.

---

## 6. Fleet overview counting

**Decision**: Implement `compute_fleet_counts(deployments: list[dict]) -> FleetCounts` in `frontend/src/ui/fleet_counts.py` with explicit mapping from spec FR-003; filter `deleted` from list before counting when `show_terminated` is False.

**Rationale**: Testable pure function; single source of truth for overview + list filter consistency.

**Alternatives considered**:
- Count from API aggregate endpoint — rejected; FR-013 forbids backend changes.

---

## 7. Show terminated toggle

**Decision**: `st.checkbox("Show terminated", key="show_terminated")` above deployment list; when False, filter `status != "deleted"`; when True, render deleted rows with `st.caption` de-emphasis and disabled copy/actions.

**Rationale**: FR-014; no backend change required.

---

## 8. Sidebar settings layout

**Decision**: `render_sidebar()` in new `sidebar.py`: always-visible username + Sign Out; `with st.expander("Settings", expanded=False):` containing existing `render_gcp_credentials_section` and `render_lightning_ai_credentials_section` bodies (forms unchanged).

**Rationale**: Clarification option C; reuses existing credential components (constitution VI — minimal change).

**Alternatives considered**:
- Duplicate form code — rejected.
- `st.tabs` inside sidebar — rejected; cramped on narrow widths.

---

## 9. Branding cleanup

**Decision**: Remove emoji from `page_icon` (use `None` or neutral icon path), `st.title`, tab labels, banners, hardware labels, and empty-state copy. Replace “My Upload” emoji badge with text **Uploaded**.

**Rationale**: FR-002, SC-002; tests currently assert `My Upload**` — update to `Uploaded` label per professional copy requirement.

---

## 10. Testing strategy

**Decision**: TDD via `streamlit.testing.v1.AppTest` — update tab label assertions, add tests for fleet metric labels, `show_terminated` filter, four-tab order, and sidebar Settings expander presence. Extract `compute_fleet_counts` for unit tests in `frontend/tests/unit/test_fleet_counts.py`.

**Rationale**: Constitution IV/V; SC-005 requires zero regression on existing workflow tests.

**Alternatives considered**:
- Visual snapshot tests only — rejected; not deterministic in CI.
