# Feature Specification: GPU / CPU Hardware Selector for Public Model Deployment

**Feature Branch**: `008-gpu-cpu-deploy`  
**Created**: 2026-05-10  
**Status**: Draft  
**Input**: User description: "I want to enable users to pick GPU or CPU while deploying public models from huggingface. Users should be able to select either of them. Then, backend will use two different path for them. TGI-CPU is already done but has some legacy named files. Do not make major edits on CPU path. Create GPU path with vLLM. Use https://github.com/Lightning-AI/LitServe for GPU path. Be careful with user feedback on the app."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Select CPU and Deploy a Public Model (Priority: P1)

A logged-in user with valid GCP credentials navigates to the **Deploy a Public Repository** section. They enter a HuggingFace model ID, fetch its metadata, and are presented with a **CPU / GPU** hardware selector before initiating the deployment. They select **CPU** and click Deploy. The platform routes the deployment through the existing TGI-CPU inference path and shows live progress messages while the deployment is being provisioned.

**Why this priority**: CPU deployment already works end-to-end and is the most risk-free path. Wiring the selector to the existing CPU path is the minimum viable change that delivers the hardware-selector feature with zero regression risk.

**Independent Test**: Can be fully tested by entering a valid public HF model ID → selecting CPU → clicking Deploy, and verifying that the system creates a deployment record with `hardware_type = cpu` and the orchestrator uses the TGI-CPU manifest generator. Delivers a working selector UI + CPU routing without needing the GPU path.

**Acceptance Scenarios**:

1. **Given** a logged-in user with valid GCP credentials and a valid public HF model ID entered, **When** the user clicks "Fetch Repository Info" and then selects CPU and clicks Deploy, **Then** the platform creates a deployment record tagged `cpu`, shows a spinner with live status text (e.g. "Deploying CPU inference server…"), and transitions through `queued → deploying → running`.
2. **Given** a user who has selected CPU, **When** the deployment enters the provisioning phase, **Then** the status message displayed in the UI clearly states it is a CPU deployment (not GPU), so the user is never confused about what is running.
3. **Given** a user who submits a CPU deploy request, **When** the backend processes it, **Then** the TGI-CPU Kubernetes manifest is applied (not the GPU/vLLM path), preserving all existing CPU-path behaviour without any breaking changes.

---

### User Story 2 — Select GPU and Deploy a Public Model via LitServe + vLLM (Priority: P2)

A logged-in user with valid GCP credentials selects **GPU** when deploying a public HF model. The platform routes the request to a new GPU inference path that generates a LitServe-based Kubernetes manifest running vLLM as the inference backend on an NVIDIA GPU node. The user sees GPU-specific status messages (e.g. "Deploying GPU inference server via vLLM…") throughout the provisioning lifecycle.

**Why this priority**: GPU support is the primary new capability this feature delivers, but it depends on the selector UI (P1) being in place first.

**Independent Test**: Can be fully tested by selecting GPU → clicking Deploy → verifying that a Kubernetes manifest for a LitServe + vLLM container is generated (separate from the TGI-CPU manifest), and that the deployment record is tagged `gpu`. End-to-end can be validated with the FakeGCPProvider in contract tests without real cloud calls.

**Acceptance Scenarios**:

1. **Given** a logged-in user with valid GCP credentials, **When** they select GPU and click Deploy, **Then** the backend generates a LitServe + vLLM Kubernetes manifest (distinct from the TGI-CPU manifest) and records `hardware_type = gpu` on the deployment row.
2. **Given** a GPU deployment in progress, **When** the orchestrator applies the manifest and waits for the pod to become ready, **Then** status messages shown in the UI are GPU-specific (e.g. "Deploying GPU inference server via vLLM…", "Waiting for GPU node to schedule…").
3. **Given** a GPU deployment that reaches the `running` state, **When** the user sends an inference request, **Then** the request is forwarded to the LitServe / vLLM endpoint and a valid response is returned.

---

### User Story 3 — Clear User Feedback During and After Hardware Selection (Priority: P3)

At every stage of the deployment flow — before selection, during provisioning, and after completion or failure — the UI gives the user accurate, hardware-aware feedback. The platform never shows generic or misleading messages (e.g. always mentioning GPU even for a CPU deploy). Errors produced by the GPU path (e.g. quota exhausted for GPU nodes) are surfaced with actionable language distinct from CPU errors.

**Why this priority**: Correct feedback is critical for user trust, but it is additive and does not block the core CPU/GPU routing.

**Independent Test**: Can be fully tested by running a CPU deploy and a GPU deploy in sequence and asserting that the spinner text, success message, and deployment detail all reflect the correct hardware type chosen.

**Acceptance Scenarios**:

1. **Given** a user who has not yet selected a hardware type, **When** they view the Deploy section after fetching model info, **Then** the UI displays a clearly labelled CPU / GPU toggle or radio group (not two separate unnamed buttons) so the choice is unambiguous.
2. **Given** a CPU deployment in any non-terminal state, **When** the user views the deployment detail, **Then** no GPU-related labels or icons are shown.
3. **Given** a GPU deployment that fails due to insufficient GPU quota, **When** the user views the failure message, **Then** the message explicitly mentions "GPU quota" and suggests either switching to CPU or requesting a quota increase.

---

### Edge Cases

- What happens when the user changes the hardware selector after fetching model info but before clicking Deploy? The most recently selected hardware type is used; there is no stale-state risk.
- What if the selected model is too large for CPU (e.g. exceeds the CPU node's memory limit)? The deployment enters `failed` with a message specific to CPU resource limits.
- What if GCP has no available GPU quota in the selected region? The orchestrator surfaces a `GCPQuotaError` with a GPU-specific message; the deployment is marked `failed` and the user is told they can retry with CPU.
- What if neither CPU nor GPU is selected when the user clicks Deploy? The deploy button is disabled until a hardware type is selected; submission without selection is not possible.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Deploy a Public Repository UI MUST present a hardware selector (CPU or GPU) before the Deploy button becomes clickable.
- **FR-002**: The hardware selector MUST default to no selection; users MUST explicitly choose before deploying.
- **FR-003**: The `DeployRequest` payload sent to `POST /api/deployments` MUST include a `hardware_type` field with values `"cpu"` or `"gpu"`.
- **FR-004**: The backend MUST persist `hardware_type` on the deployment record so status polling and UI rendering can reflect the correct hardware.
- **FR-005**: When `hardware_type = cpu`, the orchestrator MUST use the existing TGI-CPU Kubernetes manifest generator without any breaking changes to its logic or file structure (legacy file names are acceptable and MUST NOT be renamed in this feature).
- **FR-006**: When `hardware_type = gpu`, the orchestrator MUST generate and apply a new Kubernetes manifest that runs a LitServe inference server with vLLM as the backend on a GPU-capable node (NVIDIA L4 or equivalent).
- **FR-007**: The GPU manifest MUST request at least one NVIDIA GPU resource limit in the Kubernetes `resources` spec so GKE Autopilot schedules the pod on a GPU node.
- **FR-008**: Live status messages during provisioning MUST be hardware-specific: CPU deploys show CPU-centric messages; GPU deploys show GPU-centric messages.
- **FR-009**: The Deploy button in the public-repo section MUST be disabled (or hidden) until the user has selected a hardware type AND the model info has been fetched.
- **FR-010**: The existing mock-deploy flow for personal models (feature 004/005/006) MUST remain unchanged; the hardware selector introduced in this feature applies only to the public-repo real-deploy flow.
- **FR-011**: On failure of a GPU deployment due to quota exhaustion, the status message MUST include "GPU quota" and recommend switching to CPU or requesting a quota increase.
- **FR-012**: The inference proxy endpoint (`POST /api/deployments/{id}/inference`) MUST work for both CPU and GPU deployments; the backend should not need to know the hardware type to forward requests.

### Key Entities

- **DeployRequest** (extended): HuggingFace model ID + `hardware_type` (cpu | gpu) + force flag.
- **DeploymentRow** (extended): Persists `hardware_type` alongside existing fields; used by the orchestrator to select the manifest generator.
- **TGI-CPU Manifest** (existing, unchanged): Kubernetes manifest for HuggingFace TGI on CPU (`vllm_manifest.py` — legacy name retained).
- **LitServe-GPU Manifest** (new): Kubernetes manifest for LitServe + vLLM on an NVIDIA GPU node.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select a hardware type and initiate a public-model deployment in under 60 seconds from first page load (excluding GCP provisioning time).
- **SC-002**: 100% of CPU deployments continue to succeed without any regressions in the existing TGI-CPU path after this feature is shipped (verified by running the existing contract and integration test suite).
- **SC-003**: GPU deployments that reach `running` state successfully respond to inference requests forwarded through the existing proxy endpoint.
- **SC-004**: Every deployment detail visible in the UI correctly reflects the hardware type chosen at deploy time — no CPU deployment shows GPU labels or vice versa.
- **SC-005**: Contract tests for the GPU deployment path achieve the same coverage level as the CPU path (happy path, quota failure, auth failure, duplicate model) using the FakeGCPProvider — no real cloud calls required.
- **SC-006**: The Deploy button cannot be activated without a hardware-type selection; zero accidental deployments without an explicit hardware choice.

---

## Assumptions

- The existing TGI-CPU manifest generator in `vllm_manifest.py` is **not renamed or refactored** in this feature; the file name's legacy mismatch is a known tech debt item accepted by the team.
- GKE Autopilot in the user's configured region supports on-demand NVIDIA L4 GPU nodes (or equivalent); no additional GCP node pool configuration beyond a GPU resource request is required.
- LitServe is installed as a Python dependency inside the GPU inference container image, not in the backend service itself; the backend only generates the Kubernetes manifest.
- The vLLM backend used in the GPU path serves a TGI/OpenAI-compatible HTTP API on port 8000, so the existing inference proxy can forward requests without modification.
- The hardware selector applies exclusively to the **Deploy a Public Repository** flow. The personal-model mock-deploy flow (which already has its own CPU/GPU buttons for simulated deployments) is out of scope for this feature.
- Mobile/responsive layout of the hardware selector is out of scope for v1; standard Streamlit column layout is sufficient.
- No additional authentication or quota-check API calls are made before the user selects hardware; GCP quota validation happens naturally during provisioning and surfaces as a `failed` deployment with an actionable message.
