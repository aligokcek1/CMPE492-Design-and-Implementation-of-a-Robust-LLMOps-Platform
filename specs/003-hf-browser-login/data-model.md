# Data Model: Hugging Face Browser Login

**Feature**: 003-hf-browser-login
**Date**: 2026-03-14

## Extended Entities

*(This builds upon the existing entities defined in `002-llm-hf-inference`)*

### 1. Hugging Face OAuth Application (Configuration)
The application credentials registered with Hugging Face to enable the OAuth flow. Stored in `.env`.
- `HF_CLIENT_ID` (String): The public identifier for the registered app.
- `HF_CLIENT_SECRET` (String): The secret key used to authenticate the app during token exchange.
- `HF_REDIRECT_URI` (String): `http://localhost:8501/` (Must match HF settings).

### 2. OAuth State Session (Ephemeral)
Temporary state stored in Streamlit's `st.session_state` to prevent CSRF attacks.
- `oauth_state` (String): A cryptographically secure random string generated before redirecting to HF. Checked against the `state` parameter returned in the callback.

### 3. Hugging Face Account (Updated)
Represents the user's connection status.
- `hf_token` (String): The OAuth Access Token stored persistently in `.env` (overwriting any previous manual token).
- `token_type` (String): Typically "Bearer" or "Access". (Implicitly handled by the `huggingface_hub` client).
- `scopes` (List[String]): The permissions granted by the token (must include `read` and `write`).

### State Transitions (Authentication Lifecycle)
1. **Unauthenticated**: No valid token in `.env`. UI shows "Login with Hugging Face" button.
2. **Authorizing**: User clicks button, `oauth_state` is generated, and user is redirected to `huggingface.co/oauth/authorize`.
3. **Callback Processing**: User returns to `http://localhost:8501/?code=...&state=...`.
   - If `state` matches `session_state.oauth_state`: Proceed.
   - Else: Fail (CSRF suspected).
4. **Token Exchange**: App sends `code` to `huggingface.co/oauth/token` to get the access token.
5. **Authenticated**: App writes token to `.env` using `dotenv.set_key()`. App state changes to "Connected".
6. **Token Revoked/Expired**: If an API call (e.g., uploading a model) returns a 401/403, the app intercepts the error, clears the `.env` token, and transitions back to **Unauthenticated**.
