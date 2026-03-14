# Feature Specification: Hugging Face Browser Login

**Feature Branch**: `003-hf-browser-login`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "now I want to create a login feature with huggingface from the browser"  
**Runtime**: Streamlit app at `http://localhost:8501`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browser-Based OAuth Login (Priority: P1)

As a user, I want to click a "Login with Hugging Face" button that redirects me to the Hugging Face website to authorize the application, rather than manually copy-pasting a personal access token.

**Why this priority**: Improves user experience and security by using standard OAuth flows instead of manual token handling.

**Independent Test**: Can be fully tested by verifying the user is redirected to Hugging Face, can authorize the app, and is successfully redirected back to the application in a "Connected" state.

**Acceptance Scenarios**:

1. **Given** an unauthenticated state, **When** I click "Login with Hugging Face", **Then** I am redirected to the Hugging Face authorization page.
2. **Given** I am on the Hugging Face authorization page, **When** I grant permission, **Then** I am redirected back to the app and my account is marked as "Connected".
3. **Given** I am on the Hugging Face authorization page, **When** I deny permission, **Then** I am redirected back to the app with an authentication failure message.

---

### Edge Cases

- **User Denies Access**: How does the system handle the user clicking "Cancel" or "Deny" on the Hugging Face authorization page? (Should show a clear, friendly error message and return to the login screen).
- **Callback Tampering**: How does the system ensure the OAuth callback hasn't been intercepted or tampered with (e.g., using state parameters)?
- **Expired/Revoked Grants**: If the user revokes the OAuth grant from their Hugging Face account settings, the next API call will return a 401/403 response. The system MUST detect this, clear the `HF_TOKEN` from `.env`, update the UI to an unauthenticated state, and prompt the user to re-login.

## Clarifications

### Session 2026-03-14

- Q: What OAuth scopes should the application request from Hugging Face during the authorization flow? → A: `read` + `write` — profile info, read and write/upload to repos.
- Q: Where should the retrieved OAuth access token be stored persistently? → A: `.env` file — overwrite `HF_TOKEN` in `.env` at runtime.
- Q: What should happen when the stored OAuth access token is found to be expired or revoked? → A: Detect on next API call failure (401/403); clear token from `.env` and prompt re-login.
- Q: What is the local callback URL / redirect URI that the Streamlit app will handle for the OAuth callback? → A: `http://localhost:8501/` (Streamlit app on port 8501; `st.query_params` intercepts `code` and `state` on any page load of the root URL).
- Q: How should the OAuth callback be handled in Streamlit (which has no native server-side routing)? → A: Use `st.query_params` to read `code` and `state` query parameters from the Streamlit page URL on load.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a "Login with Hugging Face" button in the Account Management section.
- **FR-002**: System MUST initiate an OAuth2 authorization code flow with Hugging Face upon button click, requesting `read` and `write` scopes (profile info, repo read and write/upload access).
- **FR-003**: System MUST handle the OAuth callback by reading `code` and `state` query parameters via `st.query_params` when Streamlit loads at `http://localhost:8501/`. This URI MUST be registered as the redirect URI in the Hugging Face OAuth application settings.
- **FR-004**: System MUST exchange the authorization code for an access token securely.
- **FR-005**: System MUST handle OAuth errors gracefully (e.g., user denial, invalid state).
- **FR-006**: System MUST persistently store the retrieved access token by overwriting the `HF_TOKEN` value in the `.env` file at runtime, replacing any previously stored manual token.
- **FR-007**: System MUST use the retrieved OAuth access token for all subsequent Hugging Face API interactions (uploading models, fetching repos) defined in previous features.
- **FR-008**: System MUST detect a 401/403 response from the Hugging Face API, clear the stored `HF_TOKEN` from `.env`, transition the UI to an unauthenticated state, and prompt the user to re-login.
- **FR-009 (Update to legacy FR-010/013)**: The application MUST continue to operate in a single-user local mode. The OAuth token stored in `.env` satisfies the security requirement previously handled by the manual token.

### Key Entities

- **OAuth State**: A secure, random string used to prevent CSRF attacks during the OAuth flow.
- **OAuth Access Token**: The token retrieved from Hugging Face after a successful login flow, used to authenticate API requests. Granted with `read` and `write` scopes covering profile info, repo read access, and repo write/upload access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the Hugging Face login flow in under 1 minute (assuming they are already logged into HF in their browser).
- **SC-002**: 100% of successful OAuth callbacks result in a verified, connected state within the application.
- **SC-003**: Manual token entry is no longer the primary or required method for connecting an account.
