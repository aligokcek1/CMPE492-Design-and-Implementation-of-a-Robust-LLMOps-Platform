import sys
from pathlib import Path

# Ensure the project root is on sys.path when launched via `streamlit run src/app.py`
_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

from src import config
from src.cache import ModelCache
from src.hf_client import HFAuthenticationError, HFClient
from src.ui import auth_view, deploy_view, upload_view

st.set_page_config(page_title="LLM Inference App", layout="wide")

config.load_config()

_cache = ModelCache()
_cache.init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _on_connect_change(connected: bool) -> None:
    st.session_state["is_connected"] = connected
    if connected:
        _sync_cache()


def _handle_auth_revocation() -> None:
    """Clear a revoked/expired token and transition the UI to unauthenticated (FR-008)."""
    config.clear_hf_token()
    st.session_state["is_connected"] = False
    st.warning(
        "Your Hugging Face session has expired or been revoked. "
        "Please log in again."
    )


def _sync_cache() -> None:
    """Sync local model registry against actual HF repos. Detects 401/403 (FR-008)."""
    token = config.get_hf_token()
    if not token:
        return
    try:
        client = HFClient(token)
        # T014: HFClient is freshly instantiated after OAuth success (post-rerun),
        # so it always picks up the token written to the environment by save_hf_token().
        client.call_api_or_raise()
        user_repos = client.list_user_repos()
        _cache.sync_with_hf(user_repos)
    except HFAuthenticationError:
        _handle_auth_revocation()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# OAuth Callback Handling — T011, T012, T013, T015 (FR-003, FR-004, FR-005, FR-006)
# ---------------------------------------------------------------------------


def _handle_oauth_callback(query_code: str, query_state: str) -> None:
    """
    Exchange the authorization code for an access token.
    Validates state, saves token, and transitions to connected state on success.
    Shows a user-friendly error on state mismatch or exchange failure (FR-005).
    """
    client_id = config.get_oauth_client_id()
    client_secret = config.get_oauth_client_secret()
    redirect_uri = config.get_oauth_redirect_uri()

    if not client_id or not client_secret:
        st.error(
            "OAuth credentials are not configured. "
            "Cannot complete login. Check your `.env` file."
        )
        st.query_params.clear()
        return

    from src.oauth import pop_pending_state

    # Prefer the file-based state (survives the browser redirect away from Streamlit).
    # Fall back to session_state for environments where the redirect stays in-session.
    saved_state = pop_pending_state() or st.session_state.get("oauth_state", "")
    callback_url = f"{redirect_uri}?code={query_code}&state={query_state}"

    try:
        from src.oauth import HFOAuthService

        oauth = HFOAuthService(client_id, client_secret, redirect_uri)
        token = oauth.fetch_token(callback_url, saved_state)
        access_token = token.get("access_token")

        if not access_token:
            st.error("Login failed: no access token returned by Hugging Face.")
            _clear_oauth_session()
            return

        # T013: persist token and transition to connected state
        config.save_hf_token(access_token)
        st.session_state["is_connected"] = True
        _clear_oauth_session()
        st.rerun()

    except ValueError as exc:
        # T015: state mismatch (CSRF) or other validation error
        st.error(f"Login failed: {exc}")
        _clear_oauth_session()
    except Exception as exc:
        st.error(f"Authentication error during login: {exc}")
        _clear_oauth_session()


def _clear_oauth_session() -> None:
    """Remove OAuth ephemeral state and clear query params."""
    st.session_state.pop("oauth_state", None)
    st.query_params.clear()


# ---------------------------------------------------------------------------
# Bootstrap: check for OAuth callback or existing token
# ---------------------------------------------------------------------------


query_code = st.query_params.get("code")
query_state = st.query_params.get("state")

if query_code and query_state:
    # T011: OAuth callback detected — process before rendering anything else
    _handle_oauth_callback(query_code, query_state)
    st.stop()

if "is_connected" not in st.session_state:
    token = config.get_hf_token()
    st.session_state["is_connected"] = bool(token)
    if st.session_state["is_connected"]:
        _sync_cache()


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------


st.title("LLM Inference App")
st.sidebar.title("Navigation")

_pages = ["Account", "Upload Model", "Deploy & Inference"]
if not st.session_state.get("is_connected"):
    _pages = ["Account"]

_page = st.sidebar.radio("Go to", _pages)

if _page == "Account":
    auth_view.render(_on_connect_change)
elif _page == "Upload Model":
    upload_view.render()
elif _page == "Deploy & Inference":
    deploy_view.render()
