# Tasks: Hugging Face Browser Login

**Input**: Design documents from `/specs/003-hf-browser-login/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per Constitution Principle II (TDD). Red-Green-Refactor cycle must be followed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure updates for the new feature.

- [x] T001 Update `requirements.txt` to include `requests_oauthlib`.
- [x] T001b [P] Add `HF_CLIENT_ID`, `HF_CLIENT_SECRET`, and `HF_REDIRECT_URI` to the `.env` template (`.env.example`) and update `src/config.py` to load and expose these three values alongside `HF_TOKEN`. This is a prerequisite for `HFOAuthService.__init__`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T002 [P] Write unit tests for `.env` updates (`save_hf_token`, `clear_hf_token`) in `tests/unit/test_config.py`.
- [x] T003 Implement `save_hf_token` and `clear_hf_token` in `src/config.py` using `dotenv.set_key`.
- [x] T004 [P] Write unit tests for `HFOAuthService` in `tests/unit/test_oauth.py`.
- [x] T005 Create `src/oauth.py` and implement `HFOAuthService` initialization and `get_authorization_url()`.
- [x] T006 Implement `fetch_token()` in `src/oauth.py` handling token exchange and state validation.

**Checkpoint**: Foundation ready - the OAuth underlying service and configuration modifiers are functional.

---

## Phase 3: User Story 1 - Browser-Based OAuth Login (Priority: P1) 🎯 MVP

**Goal**: As a user, I want to click a "Login with Hugging Face" button that redirects me to the Hugging Face website to authorize the application.
**Independent Test**: Can be fully tested by verifying the user is redirected to Hugging Face, can authorize the app, and is successfully redirected back to the application in a "Connected" state.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Write Streamlit integration test for the new OAuth login button flow in `tests/integration/test_auth_view.py`.
- [x] T008 [P] [US1] Write Streamlit integration test for the callback handling and token extraction in `tests/integration/test_app.py`.
- [x] T008b [P] [US1] Write unit tests for 401/403 detection and token-clearing logic in `tests/unit/test_hf_client.py`: mock an API call that returns 401/403, assert `clear_hf_token()` is called and the return value signals an unauthenticated state (covers FR-008). Must be observed failing before T016.

### Implementation for User Story 1

- [x] T009 [US1] Update `src/ui/auth_view.py` to replace the manual token input field with a "Login with Hugging Face" button.
- [x] T010 [US1] Link the login button to generate the OAuth URL via `HFOAuthService`, store `oauth_state` in `st.session_state`, and use `st.markdown` with an HTML redirect or `st.query_params` trick to redirect the user to HF.
- [x] T011 [US1] Update `src/app.py` to check for `code` and `state` in `st.query_params` upon load.
- [x] T012 [US1] Implement callback logic in `src/app.py` to call `HFOAuthService.fetch_token()`, validating against `session_state.oauth_state`.
- [x] T013 [US1] On successful fetch in `src/app.py`, save the token via `save_hf_token()`, clear query params, and update app state to "Connected".
- [x] T014 [US1] Update `src/hf_client.py` initialization or add a reload method to ensure the client uses the newly stored `.env` token immediately after OAuth success, satisfying FR-007.
- [x] T015 [US1] Implement inline error handling in `src/app.py` or `src/ui/auth_view.py` for user denial ("Cancel" clicked on HF page) or state mismatch (CSRF).
- [x] T016 [US1] Implement 401/403 detection (FR-008) in `src/hf_client.py` and `src/app.py` to clear token and prompt re-login when token is revoked/expired.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The app supports full OAuth browser login.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and cleanup

- [x] T017 [P] Update `README.md` with the new OAuth application registration instructions from `quickstart.md`.
- [x] T018 Code cleanup, removing old manual token logic if entirely obsolete.

---

## Dependencies & Execution Order

- **Phase 1 & Phase 2**: Must be completed first in sequence to provide the OAuth backend.
- **Phase 3 (US1)**: Depends on Phase 2. Delivers the core UI and routing for OAuth. Tests (T007, T008, T008b) must be written and observed failing before implementation tasks (T009–T016).
- **Phase 4 (Polish)**: Runs last.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2: Foundational OAuth classes.
2. Complete Phase 3: Integrate OAuth into Streamlit UI and routing.
3. **STOP and VALIDATE**: Test the full browser redirect flow locally.

### Task ID Reference (Post-Remediation)

| ID | Phase | Description |
|----|-------|-------------|
| T001 | 1 | Update requirements.txt |
| T001b | 1 | Add OAuth credentials to .env template & config.py |
| T002–T006 | 2 | Foundational OAuth service and config functions |
| T007, T008, T008b | 3 (Tests) | Integration/unit tests — must fail before implementation |
| T009–T016 | 3 (Impl) | OAuth UI, routing, callback, error handling |
| T017–T018 | 4 | README update and code cleanup |
