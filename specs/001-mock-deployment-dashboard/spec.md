# Feature Specification: Mock Deployment Dashboard

**Feature Branch**: `001-mock-deployment-dashboard`  
**Created**: 2025-03-10  
**Status**: Draft  
**Input**: User description: "Build a mock deployment application with a backend API and a frontend dashboard..."

## Clarifications

### Session 2025-03-10

- Q: Can the mock deployment ever fail, or does it always complete successfully? → A: Always succeed; simulated deployment always reaches "Serving"
- Q: What HTTP status should the status endpoint return for an unknown job_id? → A: 404 Not Found
- Q: When should the dashboard stop polling? → A: When status is "Serving" OR when status endpoint returns an error (e.g., 404)
- Q: Should the Deploy button be disabled while a deployment is in progress? → A: No; allow multiple deployments; user can start another while one is in progress
- Q: For invalid or missing parameters on the deploy endpoint, what HTTP status should the API return? → A: 422 Unprocessable Entity with structured error details in body

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initiate Model Deployment (Priority: P1)

A user selects a source type (local or Hugging Face) and hardware preference (GPU or CPU), then triggers a deployment. The system accepts the request, generates a unique job identifier, starts the deployment process in the background, and immediately returns the job ID so the user can track progress.

**Why this priority**: Core value of the feature; without deployment initiation, no other functionality is possible.

**Independent Test**: Can be fully tested by sending a deployment request with valid parameters and verifying an immediate response containing a job identifier. Delivers value by enabling programmatic deployment initiation.

**Acceptance Scenarios**:

1. **Given** the deployment service is available, **When** the user submits a deployment request with source_type "local" and hardware "gpu", **Then** the system returns a job_id and the deployment process begins in the background.
2. **Given** the deployment service is available, **When** the user submits a deployment request with source_type "huggingface" and hardware "cpu", **Then** the system returns a job_id and the deployment process begins in the background.
3. **Given** a deployment has been initiated, **When** the user requests the status for that job_id, **Then** the system returns the current deployment state (e.g., Uploading, Provisioning, Starting Engine, or Serving).

---

### User Story 2 - Monitor Deployment via Dashboard (Priority: P2)

A user opens the deployment dashboard in a browser, fills out a form with source type and hardware options, and clicks Deploy. The dashboard sends the request, receives a job ID, and automatically polls for status updates. The user sees the current status and a loading indicator until the deployment reaches the "Serving" state.

**Why this priority**: Provides the primary user-facing experience; depends on backend API from US1.

**Independent Test**: Can be tested by loading the dashboard, submitting the form, and observing status updates until completion. Delivers value by giving users a visual, interactive way to deploy and monitor.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** they select "local" from the Source Type dropdown and "gpu" from the Hardware dropdown and click Deploy, **Then** the form submits the request and the user sees a loading indicator with status text.
2. **Given** a deployment has been initiated from the dashboard, **When** the system polls for status, **Then** the user sees status updates (e.g., Uploading → Provisioning → Starting Engine → Serving) at regular intervals.
3. **Given** the deployment reaches the "Serving" state, **When** the status is displayed, **Then** the loading indicator stops and the user sees the final status.

---

### Edge Cases

- What happens when the user requests status for a non-existent job_id? The system returns 404 Not Found; the dashboard stops polling and displays an error.
- What happens when the user submits a deployment request with invalid or missing parameters? The system returns 422 Unprocessable Entity with structured error details in the response body and does not create a job.
- How does the system handle multiple concurrent deployments? Each receives a unique job_id and progresses independently.
- Does the simulated deployment ever fail? No — the mock always completes successfully and reaches "Serving".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose an endpoint that accepts deployment requests via a JSON payload containing `source_type` (values: "local" or "huggingface") and `hardware` (values: "gpu" or "cpu"). For invalid or missing parameters, the system MUST return 422 Unprocessable Entity with structured error details in the response body.
- **FR-002**: The system MUST generate a unique `job_id` for each deployment request and return it immediately in the response.
- **FR-003**: The system MUST process each deployment as a background task that progresses through distinct states: Uploading, Provisioning, Starting Engine, and finally Serving.
- **FR-004**: The system MUST expose an endpoint that returns the current deployment state for a given `job_id`, and MUST return 404 Not Found for an unknown `job_id`.
- **FR-005**: The system MUST serve a web dashboard at the root path that allows users to initiate deployments and view status.
- **FR-006**: The dashboard MUST include a form with a Source Type dropdown (local, huggingface), a Hardware dropdown (gpu, cpu), and a Deploy button. The form MUST remain enabled during deployment so users can initiate multiple deployments concurrently.
- **FR-007**: When the user clicks Deploy, the dashboard MUST send a deployment request and then poll the status endpoint at regular intervals (e.g., every 2 seconds) until the status is "Serving" or until the status endpoint returns an error (e.g., 404).
- **FR-008**: The dashboard MUST display the current status text and a loading indicator while the deployment is in progress.
- **FR-009**: The dashboard MUST present a modern, responsive user interface.

### Key Entities

- **Deployment Job**: A single deployment request. Attributes: job_id (unique identifier), source_type (local or huggingface), hardware (gpu or cpu), current state (Uploading, Provisioning, Starting Engine, Serving).
- **Deployment State**: The current phase of a job's lifecycle. Values: Uploading, Provisioning, Starting Engine, Serving.

## Assumptions

- TailwindCSS via CDN will be used for dashboard styling (user-specified).
- Deployment simulation is acceptable; no real model upload or infrastructure provisioning is required.
- Simulated deployments always succeed; no "Failed" state exists in the mock.
- Polling interval of 2 seconds is sufficient for user experience; no real-time push (e.g., WebSocket) is required for this feature.
- Job state is retained in memory; jobs are lost on application restart.
- The dashboard is the primary (and initially only) way users interact with the deployment API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate a deployment and receive a job identifier within 2 seconds of submitting the form.
- **SC-002**: Users can see status updates for their deployment within 5 seconds of the status changing.
- **SC-003**: Users can complete a full deployment flow (initiate → monitor → see Serving) in a single session without errors.
- **SC-004**: The dashboard loads and renders correctly in modern browsers without requiring a build step.
