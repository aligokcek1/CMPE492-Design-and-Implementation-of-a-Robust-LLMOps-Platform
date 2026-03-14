# Tasks: LLM Inference App with Hugging Face Integration

**Input**: Design documents from `/specs/002-llm-hf-inference/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per Constitution Principle II (TDD). Red-Green-Refactor cycle must be followed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure (`src/`, `src/ui/`, `tests/unit/`, `tests/integration/`) per implementation plan
- [X] T002 Initialize Python virtual environment and `requirements.txt` with `streamlit`, `huggingface_hub`, `python-dotenv`, `pytest`
- [X] T003 Create `src/config.py` to handle loading the `.env` file via `python-dotenv`
- [X] T004 Create `src/app.py` as the main Streamlit entry point with basic page routing structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T005 Write unit tests for SQLite database initialization in `tests/unit/test_cache.py`
- [X] T006 Implement `ModelCache.init_db()` in `src/cache.py` to create the `models` table per `data-model.md`
- [X] T007 Initialize the database on startup in `src/app.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order.

---

## Phase 3: User Story 1 - Hugging Face Account Connection (Priority: P1) 🎯 MVP

**Goal**: As a user, I want to connect my Hugging Face account to the application so that I can access my models and upload new ones.
**Independent Test**: Can be tested by verifying connection status changes from "Disconnected" to "Connected" and vice-versa after logout.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Write unit tests for `HFClient.is_valid_token()` and `HFClient.get_username()` in `tests/unit/test_hf_client.py` mocking `huggingface_hub`
- [X] T009 [P] [US1] Write Streamlit integration test for connection UI flow in `tests/integration/test_auth_view.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement `HFClient` initialization, `is_valid_token()`, and `get_username()` in `src/hf_client.py`
- [X] T011 [US1] Implement Account Management UI in `src/ui/auth_view.py` to accept HF Token, validate it via `HFClient`, and store it in `.env` via `config.py`
- [X] T012 [US1] Implement inline error handling for invalid tokens or network errors in `src/ui/auth_view.py`
- [X] T013 [US1] Implement "Disconnect" functionality in `src/ui/auth_view.py` to clear the stored token
- [X] T014 [US1] Integrate `auth_view.py` into the main `src/app.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The app can connect and disconnect from Hugging Face.

---

## Phase 4: User Story 2 - Model Upload from Multiple Sources (Priority: P1)

**Goal**: As a user, I want to upload LLM models from my local machine, my existing Hugging Face repositories, or public Hugging Face repositories to my connected Hugging Face account.
**Independent Tests**: 
- Local upload verifies new HF repo created.
- Public repo verifies reference stored in local registry with no HF repo created.

### Tests for User Story 2 ⚠️

- [X] T015 [P] [US2] Write unit tests for cache methods (`add_model`, `get_all_models`) in `tests/unit/test_cache.py`
- [X] T016 [P] [US2] Write unit tests for `HFClient.upload_local_file()` and `HFClient.verify_public_repo()` in `tests/unit/test_hf_client.py`
- [X] T017 [P] [US2] Write Streamlit integration tests for local upload and public repo selection in `tests/integration/test_upload_view.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `ModelCache.add_model()` and `ModelCache.get_all_models()` in `src/cache.py`
- [X] T019 [US2] Implement `HFClient.upload_local_file()` enforcing 500MB limit and `inference-app-[model-name]` naming convention in `src/hf_client.py`
- [X] T020 [US2] Implement `HFClient.verify_public_repo()` in `src/hf_client.py`
- [X] T021 [US2] Create Model Upload UI in `src/ui/upload_view.py` with options for Local PC and Public HF Repo
- [X] T022 [US2] Implement local file upload flow in `upload_view.py` linking `st.file_uploader`, `HFClient.upload_local_file()`, and `ModelCache.add_model()`
- [X] T023 [US2] Implement public repo reference flow in `upload_view.py` linking text input, `HFClient.verify_public_repo()`, and `ModelCache.add_model()`
- [X] T024 [US2] Add inline error handling for >500MB files, interrupted uploads, and inaccessible public repos in `src/ui/upload_view.py`
- [X] T025 [US2] Integrate `upload_view.py` into `src/app.py` ensuring it only shows when `is_connected` is True

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can connect and register/upload models.

---

## Phase 5: User Story 3 - Model Deployment and Inference Trigger (Mocked) (Priority: P2)

**Goal**: As a user, I want to trigger the deployment of my uploaded Hugging Face models and see a simulated inference response.
**Independent Test**: Verify that clicking "Deploy" shows a success status and clicking "Test Inference" shows a mocked response.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Write unit test for `ModelCache.mark_as_deployed()` in `tests/unit/test_cache.py`
- [X] T027 [P] [US3] Write Streamlit integration test for deployment and mocked inference flow in `tests/integration/test_deploy_view.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `ModelCache.mark_as_deployed()` in `src/cache.py`
- [X] T029 [US3] Create Deployment UI in `src/ui/deploy_view.py` listing models from `ModelCache.get_all_models()`
- [X] T030 [US3] Implement "Deploy to Cloud" button logic in `deploy_view.py` to update cache and show mocked success message
- [X] T031 [US3] Implement single-turn inference UI in `deploy_view.py` for deployed models (text input + fixed mocked response format)
- [X] T032 [US3] Integrate `deploy_view.py` into `src/app.py`

**Checkpoint**: All user stories should now be independently functional. The end-to-end mocked flow is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Implement `ModelCache.sync_with_hf()` in `src/cache.py` to verify local cache against actual HF user repos
- [X] T034 Integrate sync logic into `src/app.py` to run on login or manual refresh (FR-012)
- [X] T035 Code cleanup, refactoring, and ensuring strict adherence to "Clean & Concise" constitution principle
- [X] T036 Update `README.md` with setup instructions from `quickstart.md`

---

## Dependencies & Execution Order

- **Phase 1 & Phase 2**: Must be completed first in sequence.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 3 completion (requires HF connection).
- **Phase 5 (US3)**: Depends on Phase 4 completion (requires uploaded models).
- **Phase 6 (Polish)**: Runs last.

## Implementation Strategy

### Incremental Delivery (TDD Approach)
1. Write failing tests for Setup/Foundation. Implement to pass.
2. Write failing tests for US1. Implement UI/Logic to pass. -> **Deliver MVP (Connection)**
3. Write failing tests for US2. Implement UI/Logic to pass. -> **Deliver Model Registration**
4. Write failing tests for US3. Implement UI/Logic to pass. -> **Deliver End-to-End Flow**
