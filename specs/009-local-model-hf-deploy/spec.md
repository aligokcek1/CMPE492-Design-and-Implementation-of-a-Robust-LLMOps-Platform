# Feature Specification: Cloud Deploy of Uploaded Models

**Feature Branch**: `009-local-model-hf-deploy`  
**Created**: 2026-05-13  
**Status**: Draft  
**Input**: User description: "cloud deployment of locally uploaded models on huggingface"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy an Uploaded Model to Cloud (Priority: P1)

A user has already uploaded a local model folder to their personal HuggingFace repository through the platform's Upload tab. They now want to run that model as a live inference endpoint on cloud infrastructure. The platform should enable them to select their uploaded model and deploy it — CPU (GKE) or GPU (Lightning AI) — with the HuggingFace token automatically handled so the private repository can be pulled by the deployment environment.

**Why this priority**: This is the core end-to-end value of the feature. Without it, users cannot close the loop from uploading to serving. It also unlocks the rest of the feature.

**Independent Test**: Can be fully tested by uploading a small model to a personal HF repo, then deploying it using the platform's Deploy tab and receiving a successful inference response.

**Acceptance Scenarios**:

1. **Given** a user has a model successfully uploaded to their personal HF repo, **When** they navigate to the Deploy tab and select that model (from the user-model list), **Then** the platform initiates a cloud deployment using the user's HF token to authenticate model pull, and the deployment reaches `running` status.
2. **Given** a deployment of a user-uploaded model is running, **When** the user sends an inference request to the endpoint, **Then** the platform returns a valid model response.
3. **Given** the user's HF token is no longer valid at deploy time, **When** they attempt to deploy a private uploaded model, **Then** the system reports a clear authentication failure and does not create a deployment record.

---

### User Story 2 - Shortcut from Upload to Deploy (Priority: P2)

After a successful upload completes, the user is presented with an option to immediately proceed to deploy the model they just uploaded, without having to manually navigate to the Deploy tab and re-enter the repository ID.

**Why this priority**: Reduces friction in the primary workflow and decreases the chance of user error when transcribing repository IDs.

**Independent Test**: Can be fully tested by completing an upload and verifying that a "Deploy this model" action appears and pre-populates the deployment form with the correct repository ID.

**Acceptance Scenarios**:

1. **Given** an upload completes successfully, **When** the upload result is shown, **Then** a "Deploy this model" button is visible alongside the success message.
2. **Given** the user clicks "Deploy this model" on the upload result, **When** the Deploy tab opens, **Then** the repository ID field is pre-filled with the just-uploaded model's HF repository ID and hardware selection is available.

---

### User Story 3 - Distinguish Uploaded Models in Model Selector (Priority: P3)

In the Deploy tab's model selector, the user's personally uploaded models (private HF repos) are visually distinguished from public HF Hub models so the user understands which models require token-based access.

**Why this priority**: Improves clarity and reduces confusion when users have both public and private models in their account.

**Independent Test**: Can be fully tested by having a user with at least one private uploaded model and one deployed public model, and verifying the selector shows a clear grouping or label difference.

**Acceptance Scenarios**:

1. **Given** a user has at least one personally uploaded model, **When** they view the model selector in the Deploy tab, **Then** uploaded models are shown in a distinct group or with a visual label (e.g., "My Uploads").
2. **Given** a model is labeled as "My Uploads", **When** the user selects it, **Then** the system automatically marks the deployment as requiring token-authenticated HF access.

---

### Edge Cases

- What happens when a model was uploaded but later deleted from HuggingFace before the user attempts to deploy it? The pre-deploy check detects the 404 and returns "repository not found"; no deployment record is created.
- What happens if HuggingFace Hub is unreachable during the pre-deploy check? The system fails closed: the deployment is blocked and the user sees "HuggingFace Hub is currently unreachable, please retry."
- What if the user's HF repository is set to public after upload but the token is still provided? The system should proceed normally — token presence should not block deployment of public repos.
- What if the upload partially failed (some sub-folders errored)? The deploy shortcut should still appear if at least one folder or the root upload succeeded.
- What happens when two deployments of the same user-uploaded model are requested simultaneously? The existing duplicate-model confirmation (`force` flag) flow applies without change.
- What if the HF token is rotated between upload and deploy? The deployment environment will receive the token current at deploy time; a stale token error from HF should surface as a deployment failure with a descriptive message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to initiate a cloud deployment of any model that exists in their personal HuggingFace account (user-owned repos), not just public HF Hub models.
- **FR-002**: System MUST inject the authenticated user's HuggingFace access token as a transient `HF_TOKEN` environment variable into the deployment environment (GKE pod or Lightning AI job) at launch time for **every** deployment, regardless of `model_origin`. This covers user-owned private repos, gated third-party public models (e.g., Llama), and fully open public models alike. The token MUST NOT be written to any database column, log line, or persistent storage at any point in this flow.
- **FR-003**: System MUST perform a pre-deployment existence check against HuggingFace for the selected model repository, with a maximum wait of **10 seconds**, and reject the request with a descriptive error in all of the following cases: (a) the repository is not found (404), (b) the token lacks read access (403), or (c) HuggingFace Hub is unreachable or does not respond within 10 seconds — in case (c) the error message MUST read "HuggingFace Hub is currently unreachable, please retry." No deployment record is created in any rejection case.
- **FR-004**: System MUST display a "Deploy this model" shortcut action in the upload result view whenever an upload completes without a total failure (partial success counts).
- **FR-005**: When the "Deploy this model" shortcut is activated, the system MUST pre-populate the deployment form with the repository ID of the just-uploaded model.
- **FR-006**: System MUST clearly distinguish user-uploaded (private) models from publicly listed HF models in the deployment model selector, using a separate label or group heading.
- **FR-007**: System MUST propagate a deployment failure with a human-readable message when the HuggingFace token is invalid or revoked at the time the deployment environment attempts to pull the model.
- **FR-008**: System MUST determine and store `model_origin` at deploy time by comparing the owner segment of `hf_model_id` against the authenticated user's HF username: a match sets `model_origin = "uploaded"`; no match sets `model_origin = "public"`. This logic applies to both the shortcut path and manual entry. The Deployments list MUST display a "My Upload" badge on each row where `model_origin = "uploaded"`, visible without any additional user interaction.

### Key Entities *(include if feature involves data)*

- **Deployment** (extended): Existing entity, gains a `model_origin` field with values `"uploaded"` (owner segment of `hf_model_id` matches authenticated user's HF username) or `"public"` (owner is a third party). Determined at deploy time by owner-segment comparison; no separate HF Hub visibility lookup required.
- **Upload Result**: Existing response object, gains an optional `deploy_shortcut` field containing the HF repository ID to pre-populate the deploy form.
- **HF Token Secret**: A runtime secret injected as `HF_TOKEN` into every deployment environment at launch time, derived from the session's authenticated HF token. Applies to all deployments (private, gated public, and open public). Not persisted beyond the deployment job/pod startup.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from completing an upload to having a running cloud deployment of the same model in under 5 minutes, end-to-end, on a stable connection with no manual copy-pasting of repository IDs.
- **SC-002**: 100% of deployment attempts for private user-uploaded models either succeed in pulling the model from HF using the injected token, or fail with a human-readable error message — no silent failures or cryptic container crash logs exposed to the user.
- **SC-003**: The deploy shortcut is visible within the upload results view for all uploads that complete with at least one successful file transfer.
- **SC-004**: Each deployment row where `model_origin = "uploaded"` displays a "My Upload" badge visible without any additional interaction, so a user with mixed (public + private) deployments can tell them apart at a glance without extra clicks or filter changes.
- **SC-005**: Zero credentials leakage — the HF token used for model pull must not appear in deployment logs, UI responses, stored deployment records, or any other persistent artifact (applies to all deployments, not only user-uploaded ones).
- **SC-006**: The pre-deployment HuggingFace Hub existence check completes — either with a pass or a human-readable error — within 10 seconds; users never wait longer than 10 seconds before receiving feedback on whether their deploy request was accepted or rejected.

## Clarifications

### Session 2026-05-13

- Q: How should the HuggingFace token be delivered to the deployment environment (GKE pod / Lightning AI job)? → A: Inject as a transient environment variable (`HF_TOKEN`) set at job/pod launch time; never stored in DB, logs, or any persistent artifact.
- Q: Does the GPU (Lightning AI) path need to support private model deployment alongside CPU (GKE)? → A: Yes — both CPU and GPU paths must support `HF_TOKEN` injection for private model pull; if Lightning AI SDK lacks native support, an equivalent mechanism must be found.
- Q: How is `model_origin` determined at deploy time? → A: Compare the owner segment of `hf_model_id` against the authenticated user's HF username at deploy time; a match sets `model_origin = "uploaded"`, no match sets `model_origin = "public"`. This works for both shortcut and manual entry paths.
- Q: What should happen when HuggingFace Hub is unreachable during the pre-deployment existence check? → A: Fail closed — block the deployment and surface a human-readable "HuggingFace Hub is currently unreachable, please retry" error; no deployment record is created.
- Q: How should `model_origin` be surfaced in the Deployments list? → A: Show a small "My Upload" badge/label on each deployment row where `model_origin = "uploaded"`; no separate filter tab or selector required.

### Session 2026-05-13 (continued)

- Q: Should `HF_TOKEN` be injected only for user-owned models, or for all deployments? → A: Always inject `HF_TOKEN` for every deployment regardless of `model_origin`; this is harmless for fully-public models and necessary for gated third-party models (e.g., Llama) where the user has approved access.
- Q: What timeout applies to the pre-deployment HuggingFace Hub existence check before treating it as unreachable? → A: 10 seconds — balances responsiveness with tolerance for transient HF Hub latency spikes.

## Assumptions

- The user's HuggingFace access token (already stored in the session from authentication) has sufficient read permissions for their own private repositories; no additional OAuth scope negotiation is needed.
- Both the GKE TGI-CPU pod and the Lightning AI LitServe+vLLM job must support `HF_TOKEN` injection for private model pull. If the Lightning AI SDK does not natively expose an env-var mechanism for the generated job script, the implementation must find an equivalent approach (e.g., embedding the token in the generated script's environment setup); this is a hard requirement, not a best-effort.
- Model repositories uploaded through the platform are initially created as private repos on HuggingFace (matching current `create_repo` behavior with `exist_ok=True`); they may later be made public by the user outside the platform, but this spec does not manage visibility settings.
- The existing `hardware_type` selection (CPU/GPU) and credential management flows remain unchanged; this feature extends them rather than replacing them.
- The "Deploy this model" shortcut is a UI convenience; users can also deploy uploaded models through the normal Deploy tab flow by typing or selecting the repo ID manually — both paths must work.
- Mobile / non-browser access is out of scope; the Streamlit web UI is the only supported client.
