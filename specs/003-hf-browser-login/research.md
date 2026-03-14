# Phase 0: Research & Technical Decisions

**Feature**: Hugging Face Browser Login
**Date**: 2026-03-14

## Technical Context & Decisions

### 1. OAuth Implementation Strategy in Streamlit
- **Decision**: Use the `requests_oauthlib` package alongside Streamlit's native `st.query_params` and `st.login`/URL redirect capabilities.
- **Rationale**: The app is already a Streamlit monolith. Adding a full external backend (like FastAPI or Flask) just for OAuth handling violates the "Clean & Concise Implementation" constitution principle. Streamlit provides `st.query_params` which can intercept the `code` and `state` parameters sent back by Hugging Face to `http://localhost:8501/`. The Python `requests_oauthlib` simplifies the security (state verification) and token exchange processes.
- **Alternatives considered**: 
  - *Flask/FastAPI Backend*: Rejected due to unnecessary architectural complexity for a local-only tool.
  - *`authlib` directly*: Rejected; `requests_oauthlib` is slightly higher-level and more widely used for standard OAuth2 web application flows.

### 2. State Management for CSRF Protection
- **Decision**: Store the generated OAuth `state` parameter in `st.session_state` before redirecting the user to Hugging Face.
- **Rationale**: To prevent Cross-Site Request Forgery (CSRF), the OAuth flow requires passing a `state` parameter and validating it upon return. Streamlit's `session_state` is the perfect place to hold this ephemeral data across the redirect boundary since it's a local app.

### 3. Token Storage
- **Decision**: Continue using `python-dotenv`, but add a utility function to programmatically rewrite the `HF_TOKEN` key in the `.env` file.
- **Rationale**: The specification (FR-006) mandates that the retrieved token replaces any manual token in the `.env` file for persistence across restarts. We will use the `set_key` function from the `dotenv` package (part of `python-dotenv`) to safely update the `.env` file at runtime.
