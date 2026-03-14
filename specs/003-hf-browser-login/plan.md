# Implementation Plan: Hugging Face Browser Login

**Branch**: `003-hf-browser-login` | **Date**: 2026-03-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-hf-browser-login/spec.md`

## Summary

Enhance the existing LLM Inference App by adding an OAuth2 browser login flow for Hugging Face. This allows users to authenticate seamlessly via the browser instead of pasting a manual access token. The application will intercept the OAuth callback, securely exchange the authorization code for an access token, and overwrite the existing local `.env` file to persist the session.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Streamlit, `huggingface_hub`, `python-dotenv`, `requests_oauthlib` (New)  
**Storage**: `.env` file (HF Token storage; overwritten dynamically via `dotenv.set_key`)  
**Testing**: `pytest`, `unittest.mock`  
**Target Platform**: Localhost / Local PC (`http://localhost:8501`)  
**Project Type**: Streamlit Web Application (Monolith)  
**Performance Goals**: OAuth redirect and token exchange completes in < 2 seconds.  
**Constraints**: Single-user local app only. No remote backend.  
**Scale/Scope**: Single local user connecting to their personal Hugging Face account.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Security-First Cloud Readiness**: PASS. OAuth2 is the industry standard for secure delegated access. Storing the `state` parameter prevents CSRF. The resulting token is securely kept in `.env`.
- **II. Mandatory Test-Driven Development (TDD)**: PASS. The plan requires unit tests for the OAuth exchange logic and error handling before UI integration.
- **III. Clean & Concise Implementation**: PASS. Reusing the Streamlit framework via `st.query_params` avoids introducing a bloated external API layer (like Flask) just for one callback route.
- **IV. Scalable Architecture & Observability**: PASS. Architecture remains consistent with previous feature.
- **V. Practical & Iterative Delivery**: PASS. Adding OAuth provides immediate practical UX value.

## Project Structure

### Documentation (this feature)

```text
specs/003-hf-browser-login/
├── plan.md              # This file
├── research.md          # Technical decisions
├── data-model.md        # OAuth Entities 
├── contracts/           # Updated internal interfaces
└── tasks.md             # Implementation tasks (generated later)
```

### Source Code (repository root)

*(Updating existing structure)*

```text
src/
├── app.py                 # Streamlit entry point (updated to catch /callback query params)
├── config.py              # Environment and token management (updated to rewrite .env)
├── hf_client.py           # huggingface_hub wrapper
├── oauth.py               # NEW: OAuth2 authorization and token exchange logic
├── cache.py               # SQLite database operations
└── ui/                    
    ├── auth_view.py       # Updated: Replaces manual token input with OAuth button/status
    ├── upload_view.py     
    └── deploy_view.py     

tests/
├── integration/           
└── unit/                  
    ├── test_oauth.py      # NEW: Tests for OAuth state and token exchange
```

**Structure Decision**: A new `src/oauth.py` module will encapsulate the `requests_oauthlib` logic, keeping the `auth_view.py` purely focused on UI rendering and `app.py` focused on routing.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No violations. The architecture remains clean and concise.)*
