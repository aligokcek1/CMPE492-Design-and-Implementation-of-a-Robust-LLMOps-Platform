import streamlit as st

from src import config
from src.hf_client import HFClient
from src.oauth import HFOAuthService, save_pending_state


def render(on_connect_change) -> bool:
    """
    Render the Account Management UI.
    Calls on_connect_change(bool) when connection state changes.
    Returns True if currently connected.
    """
    st.header("Hugging Face Account")

    token = config.get_hf_token()

    if token:
        try:
            client = HFClient(token)
            if client.is_valid_token():
                username = client.get_username()
                st.success(f"Connected as **{username}**")
                if st.button("Disconnect"):
                    config.clear_hf_token()
                    on_connect_change(False)
                    st.rerun()
                return True
        except Exception:
            pass
        st.warning("Stored token is no longer valid. Please reconnect.")
        config.clear_hf_token()

    _render_login_button()
    return False


def _render_login_button() -> None:
    """Render the OAuth login button (FR-001). On click, redirect to HF authorization page."""
    client_id = config.get_oauth_client_id()
    client_secret = config.get_oauth_client_secret()
    redirect_uri = config.get_oauth_redirect_uri()

    st.info("Connect your Hugging Face account to get started.")

    if not client_id or not client_secret:
        st.warning(
            "OAuth credentials are not configured. "
            "Add `HF_CLIENT_ID` and `HF_CLIENT_SECRET` to your `.env` file. "
            "See `.env.example` for instructions."
        )
        return

    if st.button("Login with Hugging Face"):
        oauth = HFOAuthService(client_id, client_secret, redirect_uri)
        auth_url, state = oauth.get_authorization_url()
        # Write state to disk — session_state is lost when the browser navigates
        # away from Streamlit via the meta refresh redirect (FR-002).
        save_pending_state(state)
        st.session_state["oauth_state"] = state  # kept as a fallback
        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={auth_url}">',
            unsafe_allow_html=True,
        )
        st.stop()
