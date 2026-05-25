# Feature Specification: Production-Grade Operations Dashboard UI

**Feature Branch**: `011-streamlit-dashboard-refactor`  
**Created**: 2026-05-25  
**Status**: Draft  
**Input**: User description: "Refactor the LLMOps web client into a polished, production-grade engineering dashboard for data scientists and ML engineers. Use only native built-in UI components (no complex external web libraries). Apply wide-screen layout and clean typography. Remove emojis and casual branding from titles and navigation. Move static setup forms (user profile, cloud credentials) into an organized collapsible sidebar panel. Prioritize an operational summary (active, provisioning, failed deployments) at the top. Present each deployment as a horizontal row with metadata, color-coded status, and copyable API endpoints with compact actions. Tuck verbose telemetry, provisioning detail, and error traces into collapsible disclosures beneath each row."

## Clarifications

### Session 2026-05-25

- Q: How should primary main-area navigation be organized after credentials move to the sidebar? → A: Four workflow tabs — **Deployments** (default), **Upload Model**, **Select Model**, **Deploy**; credentials and profile only in the sidebar.
- Q: How should **deleting**, **lost**, and **deleted** deployments be counted in the fleet overview? → A: **deleting** → provisioning; **lost** → failed; **deleted** → excluded from all overview buckets.
- Q: Which controls stay in the collapsed deployment row vs. the detail disclosure? → A: **Row:** copy endpoint + Delete/Dismiss only — **Disclosure:** metrics, inference, Grafana link, provisioning messages, errors.
- Q: How should the sidebar organize profile, GCP, and Lightning AI setup? → A: **Profile/sign-out always visible**; single **Settings** expander for GCP + Lightning AI only.
- Q: Should **deleted** deployments appear in the main deployment list by default? → A: **Hide deleted by default**; provide a **Show terminated** toggle to reveal them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Scan Fleet Health at a Glance (Priority: P1)

A logged-in ML engineer opens the platform after deploying several models. The main workspace immediately shows a **fleet overview** with counts for **active** (serving), **provisioning** (queued or deploying), and **failed** deployments. They can assess overall system health without scrolling through individual cards or opening setup screens.

**Why this priority**: Operations users need situational awareness first; every other workflow assumes they can quickly see whether anything is broken or still coming up.

**Independent Test**: Can be fully tested by seeding deployments in mixed statuses and verifying the overview counts match the deployment list within one refresh cycle.

**Acceptance Scenarios**:

1. **Given** a logged-in user with deployments in **running**, **queued**, **deploying**, and **failed** states, **When** they open the **Deployments** tab (default list, **Show terminated** off), **Then** they see three distinct summary metrics labeled for active, provisioning, and failed counts that sum consistently with visible non-deleted deployments.
2. **Given** a user with zero deployments, **When** they open the operations view, **Then** the overview shows zero for all categories and a concise empty-state message directing them to deploy a model.
3. **Given** a deployment transitions from **deploying** to **running**, **When** the list refreshes, **Then** the overview moves that deployment from provisioning to active without requiring a full page reload beyond normal app refresh behavior.

---

### User Story 2 — Operate Deployments from Dense Rows (Priority: P1)

The same user scrolls to the deployment list beneath the overview. Each deployment appears as a **single horizontal row** divided into three zones: (1) hierarchical metadata (display name, repository identifier, hardware class GPU/CPU, cloud provider path), (2) a **color-coded status indicator** readable without decorative icons, and (3) the inference **API endpoint** with one-click copy plus compact row-level actions (**Delete** or **Dismiss** only). Metrics, inference testing, and Grafana access live in the collapsed-by-default detail disclosure below the row. The layout uses horizontal space efficiently on wide screens and avoids tall, blocky vertical stacks.

**Why this priority**: Deployment operations are the core daily task; the row layout is the primary deliverable of this refactor.

**Independent Test**: Can be fully tested with at least one CPU and one GPU deployment in **running** state, confirming all three row zones render correctly and the endpoint can be copied in one action.

**Acceptance Scenarios**:

1. **Given** a **running** deployment with an endpoint URL, **When** the user views its collapsed row, **Then** column one shows model name (or display name), repository ID, hardware type, and provider label; column two shows status with distinct color treatment per state; column three shows the endpoint, a one-click copy control, and **Delete** only (no Metrics or Inference buttons in the collapsed row).
2. **Given** a **running** deployment, **When** the user expands its detail disclosure, **Then** they can access metrics, inference testing, and the Grafana link without those controls appearing in the collapsed row.
3. **Given** a deployment with **model origin** indicating user upload, **When** the user views metadata, **Then** upload ownership is indicated with a professional text label (not emoji badges).
4. **Given** a **failed** deployment, **When** the user views its collapsed row, **Then** status appears in the failure color treatment and **Delete** remains available in column three where the backend allows.
5. **Given** a **lost** deployment, **When** the user views its collapsed row, **Then** **Dismiss** is available in column three without breaking row alignment.

---

### User Story 3 — Access Setup and Credentials from Sidebar (Priority: P2)

A user who needs to configure GCP credentials, Lightning AI API access, or review their signed-in profile opens a **collapsible sidebar settings panel** instead of dedicated top-level navigation tabs. Setup forms remain fully functional but no longer compete with operational views for main-screen space.

**Why this priority**: Separating configuration from operations reduces cognitive load and matches production tooling patterns, but fleet monitoring (P1) delivers value even if sidebar organization ships incrementally.

**Independent Test**: Can be fully tested by completing credential save flows entirely from the sidebar panel and confirming validation banners still surface on the main workspace when credentials are invalid.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they view the sidebar, **Then** signed-in identity and **Sign Out** are always visible without expanding any panel, and a **Settings** expander provides labeled GCP and Lightning AI credential subsections.
2. **Given** a user with invalid GCP credentials, **When** they attempt a blocked CPU action, **Then** a clear warning appears on the main workspace referencing the sidebar GCP section (without emoji tab names).
3. **Given** a user on a narrow viewport, **When** they use the sidebar, **Then** setup sections remain usable without horizontal overflow that hides primary controls.

---

### User Story 4 — Drill into Details Without Clutter (Priority: P2)

A user investigating a slow deployment or failure expands a **disclosure control directly beneath** the deployment row. Inside they find verbose content currently shown inline: provisioning status messages, infrastructure telemetry charts, inference test UI, metrics panels, and transient error traces. The collapsed default state keeps the list visually clean.

**Why this priority**: Power users need depth; casual scanning needs a pristine list. Collapsible disclosures satisfy both without sacrificing information.

**Independent Test**: Can be fully tested by expanding one running deployment's detail panel and verifying metrics, inference, and status messages appear while sibling rows stay collapsed.

**Acceptance Scenarios**:

1. **Given** a **running** deployment, **When** the user expands its detail disclosure, **Then** they can access performance metrics, inference testing, and any supplemental status text without those elements occupying the collapsed row.
2. **Given** a **deploying** deployment with a status message, **When** the row is collapsed, **Then** only the summary status is visible in column two; the full message appears inside the expanded disclosure.
3. **Given** a **failed** deployment with an error trace or diagnostic message, **When** the user expands the disclosure, **Then** the full error detail is readable with appropriate severity styling and does not push other deployment rows apart while collapsed.

---

### User Story 5 — Complete Model Lifecycle with Professional Navigation (Priority: P3)

A data scientist uploads a model, selects an existing repository, and launches a cloud deployment using **primary navigation labels without emojis or casual marketing copy**. Page title, browser tab title, and welcome text use neutral product naming appropriate for an internal engineering tool.

**Why this priority**: Branding cleanup and tab relabeling improve trust but depend less critically than operations layout (P1).

**Independent Test**: Can be fully tested by walking upload → select shortcut → deploy flow and confirming no emoji appears in navigation chrome or page headers.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the home workspace, **When** they view main navigation tabs, **Then** they see exactly four tabs in order — **Deployments** (default), **Upload Model**, **Select Model**, **Deploy** — with plain professional labels and no emoji prefixes.
2. **Given** a successful upload with deploy shortcut, **When** the user opens the deploy section, **Then** the repository field pre-populates as today without requiring the deprecated emoji-heavy tab names.
3. **Given** any authenticated view, **When** the user inspects the application title and sidebar header, **Then** neither contains emoji icons or informal course-project taglines in primary chrome (secondary footer attribution may remain in muted caption text if required by course policy).

---

### Edge Cases

- What happens when deployment count exceeds ~20 rows? The list remains scrollable; overview counts stay accurate; row layout does not wrap metadata into unreadable multi-line blocks on standard desktop widths (1280px+).
- What happens when endpoint URL is not yet assigned (**queued** / **deploying**)? Column three shows a neutral placeholder (e.g., "Pending") and copy is disabled until a URL exists.
- What happens when the user has only **deleted** or **dismissed** historical entries? **Deleted** deployments are hidden from the default list and excluded from overview buckets; users enable **Show terminated** to reveal them. **Dismissed** deployments are removed from the list entirely and excluded from counts.
- What happens when a deployment is **deleting**? It increments **provisioning** until teardown completes or the record leaves the list.
- What happens when a deployment is **lost**? It increments **failed** and remains actionable via dismiss in the deployment row.
- What happens on authentication loss mid-session? Sidebar profile reflects signed-out state; operational views redirect to login without exposing credential forms.
- What happens when metrics or inference panels error? Errors appear inside the expanded disclosure for that deployment only, not as global page failures.
- What happens for GPU vs CPU provider labeling? Metadata column always shows hardware class and provider path textually (no emoji hardware badges).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The authenticated main workspace MUST use a **wide-screen layout** that prioritizes horizontal information density over tall vertical stacks on desktop-class viewports.
- **FR-002**: Primary navigation labels, page titles, and browser tab branding MUST NOT include emoji characters or informal marketing phrases in user-visible chrome.
- **FR-003**: The platform MUST display a **fleet overview** at the top of the **Deployments** tab with three metrics, using these counting rules: **active** = **running**; **provisioning** = **queued**, **deploying**, or **deleting**; **failed** = **failed** or **lost**; **deleted** deployments MUST be excluded from all three buckets (they may still appear in the list until removed). Counts MUST update when the deployment list changes.
- **FR-004**: Each deployment MUST render as one **horizontal row** with three columns: (a) hierarchical metadata—display name, repository identifier, hardware type (GPU/CPU), cloud provider label, and upload-origin indicator when applicable; (b) status with **color-coded** visual treatment distinct per lifecycle state; (c) API endpoint with **one-click copy** when available plus **only** row-level **Delete** or **Dismiss** actions (no Metrics, Inference, or Grafana controls in the collapsed row).
- **FR-005**: Verbose per-deployment content—**metrics visualizations**, **inference testing**, **Grafana deep link**, provisioning messages, infrastructure telemetry, and error traces—MUST reside in a **collapsed-by-default disclosure** immediately below its parent row.
- **FR-006**: **Profile/session** (signed-in identity and sign-out) MUST remain **always visible** in the sidebar. **GCP credentials** and **Lightning AI credentials** MUST move out of main tabs into a single collapsible **Settings** expander with labeled subsections for each provider.
- **FR-007**: Primary main-area navigation MUST expose exactly **four top-level tabs**: **Deployments** (default landing tab), **Upload Model**, **Select Model**, and **Deploy**. Credential and profile setup MUST NOT appear as main tabs. Upload, selection, and deploy workflows MUST NOT regress existing capabilities (shortcut pre-fill, hardware selector, validation error messages).
- **FR-008**: Credential validation warnings (invalid GCP or Lightning AI keys) MUST remain visible on the main workspace when they block actions, with text pointing users to the appropriate sidebar settings subsection.
- **FR-009**: All UI MUST be built with **native platform components only**—no additional complex external front-end frameworks or component libraries beyond what the existing client already depends on.
- **FR-010**: Status presentation MUST NOT rely on emoji icons; states MUST be distinguishable by text label and color (or equivalent non-emoji indicator supported natively).
- **FR-011**: The collapsed row MUST expose only **Delete** (with confirmation flow) or **Dismiss** (for **lost** deployments) plus endpoint copy. **Metrics**, **inference testing**, and **Grafana** access MUST appear only inside the detail disclosure for eligible deployments, without enlarging the collapsed row height.
- **FR-012**: Empty, loading, and error states for the deployment list MUST use concise professional copy consistent with the new visual language (including a loading indicator while fetching deployments and a user-visible error when the list API fails).
- **FR-013**: Existing authentication, API integration, and backend behavior MUST remain unchanged; this feature refactors presentation and information architecture only.
- **FR-014**: The deployment list MUST **hide deleted** deployments by default. A **Show terminated** control MUST reveal deleted deployments in a visually de-emphasized style without affecting fleet overview counts (still excluded per FR-003). Fleet overview counts MUST be computed on the same filtered deployment set used to render the list.

### Key Entities

- **Fleet Overview**: Aggregated counts (active, provisioning, failed) derived from the user's current deployment list using FR-003 status mapping; not persisted separately.
- **Deployment Row**: A presentation unit binding one deployment's summary columns and an optional detail disclosure.
- **Metadata Column**: Human-readable model identity, technical identifiers, hardware class, provider path, and origin (uploaded vs public).
- **Status Column**: Lifecycle state with color-coded indicator and short label; long messages deferred to disclosure.
- **Actions Column**: Endpoint URL, copy control, and row-level **Delete** or **Dismiss** only.
- **Detail Disclosure**: Collapsible region holding metrics, inference UI, Grafana link, telemetry, and extended diagnostics for one deployment.
- **Sidebar Profile Strip**: Always-visible signed-in identity and sign-out control.
- **Sidebar Settings Panel**: Collapsible expander containing GCP and Lightning AI credential configuration only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a 1920×1080 display, a user with five deployments can identify active vs failed counts and locate a specific model's endpoint in **under 15 seconds** without expanding any disclosure.
- **SC-002**: **100%** of primary navigation labels and page titles visible to authenticated users contain **zero emoji** characters in user acceptance review.
- **SC-003**: At least **90%** of test participants in a five-person hallway test rate the post-refactor deployments view as "professional" or "production-like" compared to "student project" when shown side-by-side with the prior UI (binary forced choice).
- **SC-004**: Copying an endpoint URL requires **one click** from the collapsed deployment row when the endpoint exists (verified in manual test script).
- **SC-005**: All existing frontend integration tests for upload, deploy shortcut, hardware selection, deployment list actions, and metrics panels continue to pass after UI relocation (zero regressions in automated workflow tests).
- **SC-006**: With all detail disclosures collapsed, the vertical space occupied by the fleet overview plus ten deployment rows is **at least 30% less** than the pre-refactor bordered-card layout on the same viewport (measured once in acceptance screenshot comparison).

## Assumptions

- Target users are data scientists and ML engineers on desktop or laptop screens (≥1280px width); mobile-first layout is out of scope.
- "Native components only" means standard built-in layout primitives (columns, containers, metrics, expanders, sidebar, forms, buttons, code blocks) already used in the project; minimal custom styling via supported theming hooks is acceptable if it does not introduce external JS/CSS frameworks.
- Main-area navigation is four tabs: **Deployments** (default), **Upload Model**, **Select Model**, **Deploy**; credential/profile setup lives only in the sidebar panel.
- The **Deployments** tab is the default landing view after authentication and hosts the fleet overview plus deployment rows.
- Color-coded status uses accessible contrast pairs; exact palette is an implementation choice as long as states are distinguishable without emoji.
- Narrow-viewport sidebar usability (US3) is verified manually at ~1280px width per quickstart.md, not via automated AppTest.
- Course attribution text (e.g., project name in sidebar footer) may remain in de-emphasized caption form if academically required.
- No backend API changes are required; deployment data fields already exposed remain the source of truth.
- Grafana deep links and metrics charts from feature 010 move into per-deployment detail disclosures rather than being removed.

## Dependencies

- Existing authenticated session and deployment APIs (features 006–010).
- Existing metrics panel and Grafana link behavior (feature 010) repositioned under detail disclosures.
- Existing GCP and Lightning AI credential validation flows (features 007–008).
