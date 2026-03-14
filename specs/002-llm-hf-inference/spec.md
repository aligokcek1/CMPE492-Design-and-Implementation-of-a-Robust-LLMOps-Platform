# Feature Specification: LLM Inference App with Hugging Face Integration

**Feature Branch**: `002-llm-hf-inference`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "I want to build an LLM inference app that supports deploying LLM models from the local pc or from the user's connected huggingface accounts or from the public huggingface repos to the cloud, which is GCP for this project. deploying to the cloud part should be mocked for now, but huggingface connection is needed. The app should allow users to login their huggingface account so that the app can be connected. All models should be uploaded to huggingface first, then they will be deployed to cloud (in the future). Also, you should allow disconnecting the huggingface accounts. The ui should be basic. An account management section with huggingface connection displayed and the model upload part."

## Clarifications

### Session 2026-03-14

- Q: What is the Hugging Face authentication method? → A: HF User Access Token (user pastes token from HF Settings page; no OAuth browser redirect)
- Q: Where should the HF User Access Token be stored? → A: ~~Encrypted server-side session~~ **(superseded)** — see App Deployment Model below.
- Q: What is the app deployment model? → A: Localhost-only tool (runs on `localhost`; single-user; HF token stored in encrypted local config file or `.env`; no server-side session required)
- Q: What does the mocked inference UI look like? → A: Single-turn only — text input field + fixed mocked text response displayed below; no streaming, no chat history
- Q: How should connection failure (invalid token / network error) be handled? → A: Inline error in Account Management section, token field cleared, stay on same page; status remains "Disconnected"
- Q: Should User Story 2's independent test be split by source type? → A: Yes — two tests: (1) local upload verifies new HF repo created; (2) public repo verifies reference stored in local registry with no HF repo created
- Q: What does "upload from public HF repo" mean? → A: Reference only — store the public repo ID as metadata; no files are transferred to the user's account
- Q: What is the hard file size limit for local model uploads? → A: 500MB hard cap; files exceeding this are rejected at point of selection
- Q: Is LLM inference functional or mocked? → A: Fully mocked; both deployment and model responses are simulated in the UI.
- Q: Should the app maintain its own model registry or fetch dynamically from Hugging Face? → A: Hybrid approach; the app maintains a local cache for performance, which is synced with the HF API on login or manual refresh.
- Q: What is the application-level access control model? → A: The app is treated as single-user/local-only; there is no separate application login, and the HF token acts as an environmental setting rather than user auth.
- Q: How should the application handle the file upload process to Hugging Face? → A: Direct to HF; the browser uploads directly to HF using their API (presigned URLs/direct commit) to avoid bottlenecking a local backend server.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hugging Face Account Connection (Priority: P1)

As a user, I want to connect my Hugging Face account to the application so that I can access my models and upload new ones.

**Why this priority**: Essential foundation. All subsequent features depend on a connected Hugging Face account.

**Independent Test**: Can be tested by verifying connection status changes from "Disconnected" to "Connected" and vice-versa after logout.

**Acceptance Scenarios**:

1. **Given** a disconnected state, **When** I provide a valid Hugging Face User Access Token, **Then** my account should be marked as "Connected" in the Account Management section.
2. **Given** a connected state, **When** I select "Disconnect", **Then** my Hugging Face account info should be removed and status changed to "Disconnected".

---

### User Story 2 - Model Upload from Multiple Sources (Priority: P1)

As a user, I want to upload LLM models from my local machine, my existing Hugging Face repositories, or public Hugging Face repositories to my connected Hugging Face account.

**Why this priority**: Core requirement to ensure models are hosted on Hugging Face before deployment.

**Independent Tests**:
- *Local upload path*: Verify that after uploading a local file, a new repository with the expected name (`inference-app-[model-name]`) appears in the user's Hugging Face account.
- *Public repo path*: Verify that after selecting a public HF repo ID, that ID is stored as a reference in the local model registry with no new repository created in the user's HF account.

**Acceptance Scenarios**:

1. **Given** a local model file, **When** I upload it, **Then** a new repository is created (or updated) on my Hugging Face account containing the model.
2. **Given** a public Hugging Face repository ID, **When** I select it, **Then** the system stores the public repo ID as a reference (no file transfer); this reference is used directly as the deployment source.

---

### User Story 3 - Model Deployment and Inference Trigger (Mocked) (Priority: P2)

As a user, I want to trigger the deployment of my uploaded Hugging Face models and see a simulated inference response.

**Why this priority**: Validates the end-to-end flow from sourcing to "usage".

**Independent Test**: Verify that clicking "Deploy" shows a success status and clicking "Test Inference" shows a mocked response.

**Acceptance Scenarios**:

1. **Given** a model already uploaded to my Hugging Face account, **When** I select "Deploy to Cloud", **Then** the system shows a "Deployment Successful" message.
2. **Given** a "deployed" model, **When** I enter a prompt and click "Run", **Then** the system displays a fixed mocked text response in the format `"[Mocked Response] This is a simulated reply from <model-name>."` with no streaming or history.

---

### Edge Cases

- **Connection Failure**: If an invalid HF token or network failure occurs during connection, the system MUST display an inline error message in the Account Management section (e.g., `"Connection failed: invalid token or network error."`), clear the token input field, and remain on the same page. Status stays "Disconnected".
- **Upload Interruption**: If a local file upload to HF is interrupted, the system MUST show an inline error in the upload section and allow the user to retry. Partial uploads are not resumed; the upload restarts from the beginning.
- **Repository Conflicts**: If a model with the same name already exists in the user's HF account (per the naming convention in FR-007), the system MUST update (overwrite) the existing repository rather than creating a duplicate.
- **Public Repo Accessibility**: If a public HF repo ID reference is found to be inaccessible (private or deleted) at deployment validation time, the system MUST block the deployment and display an inline error: `"Model reference unreachable: <repo-id> is private or does not exist."`

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to connect their Hugging Face account by entering a **User Access Token** (obtained from the user's HF Settings page); no OAuth browser redirect is required.
- **FR-002**: System MUST allow users to disconnect their Hugging Face account, removing all stored credentials immediately.
- **FR-010**: The application MUST run as a localhost-only tool (single-user, no multi-tenancy). The HF User Access Token MUST be stored in an **encrypted local configuration file** (e.g., `~/.config/llmops/config.enc` or a `.env` file with restricted permissions). It MUST NOT be stored in plain text, in a browser, or in any remote database.
- **FR-013**: The application MUST operate in a single-user mode without requiring separate application-level authentication.
- **FR-003**: System MUST display the connection status in an "Account Management" section.
- **FR-004**: System MUST allow uploading model files from the local computer to the user's Hugging Face account. The upload MUST occur directly from the client browser to the Hugging Face API to avoid passing large files through the application backend. Local uploads are capped at **500MB**; the system MUST reject files exceeding this limit with a clear error message.
- **FR-005**: System MUST allow selecting models from the user's existing Hugging Face repositories or public Hugging Face repositories. Public repos are stored as a reference (repo ID only); no files are transferred to the user's account.
- **FR-006**: System MUST ensure that before deployment: local-sourced models are present as a repository in the user's HF account, and public-repo-sourced models are validated as accessible via their stored reference (repo ID resolves and is publicly readable).
- **FR-007**: System MUST **follow a naming convention (e.g., 'inference-app-[model-name]') and reuse/update if it already exists** when uploading models from local or public sources.
- **FR-008**: System MUST provide a "Deploy to Cloud" action that simulates a deployment to GCP.
- **FR-009**: System MUST show a mocked deployment success status for any deployment trigger.
- **FR-011**: System MUST provide a single-turn inference UI for any "deployed" model: a text input field for the prompt and a response area that displays a **fixed mocked text response** (e.g., `"[Mocked Response] This is a simulated reply from <model-name>."`). No streaming, no conversation history, no actual model compute.
- **FR-012**: System MUST implement a hybrid model registry: metadata is cached locally (e.g., in a database) for UI performance, and this cache MUST be synchronized with the user's Hugging Face account via the HF API upon login or manual refresh.

### Key Entities

- **Hugging Face Account**: Represents the user's connection status and credentials.
- **Model Registry (Local Cache)**: Database table caching model metadata (ID, source, sync status) to improve UI responsiveness.
- **Model Source**: Represents where the model originates (Local PC, User HF Repo, Public HF Repo).
- **Hugging Face Repository**: Represents the destination/hosting repo on Hugging Face.
- **Deployment Record**: A log of (mocked) deployments triggered by the user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully connect their Hugging Face account in under 30 seconds.
- **SC-002**: Local model uploads up to 500MB are accepted; uploads under 100MB complete within 2 minutes on standard broadband. Files exceeding 500MB are rejected at the point of selection with a clear error.
- **SC-003**: 100% of deployment triggers result in a visible "Success" message (mocked).
- **SC-004**: Users can disconnect their account with a single interaction, immediately revoking app access to their Hugging Face data.
