import streamlit as st
import streamlit.components.v1 as components


SESSION_TOKEN_KEY = "session_token"
SESSION_USER_KEY = "hf_username"
SESSION_EXPIRES_AT_KEY = "session_expires_at"
SESSION_COOKIE_KEY = "llmops_session_token"


def get_session_token() -> str:
    return str(st.session_state.get(SESSION_TOKEN_KEY, ""))


def get_persisted_session_token() -> str:
    try:
        cookie_val = st.context.cookies.get(SESSION_COOKIE_KEY)
    except Exception:
        return ""
    if cookie_val is None:
        return ""
    return str(cookie_val)


def _render_cookie_script(script: str) -> None:
    components.html(
        f"""
        <script>
        {script}
        </script>
        """,
        height=0,
    )


def sync_session_cookie() -> None:
    token = get_session_token()
    persisted = get_persisted_session_token()

    if token and token != persisted:
        escaped = token.replace("\\", "\\\\").replace("'", "\\'")
        _render_cookie_script(
            f"document.cookie = '{SESSION_COOKIE_KEY}={escaped}; path=/; max-age=604800; SameSite=Lax';"
        )
        return

    if not token and persisted:
        _render_cookie_script(
            f"document.cookie = '{SESSION_COOKIE_KEY}=; path=/; max-age=0; SameSite=Lax';"
        )


def set_session(
    *,
    session_token: str,
    username: str,
    expires_at: str | None = None,
) -> None:
    st.session_state[SESSION_TOKEN_KEY] = session_token
    st.session_state[SESSION_USER_KEY] = username
    st.session_state["is_authenticated"] = True
    if expires_at:
        st.session_state[SESSION_EXPIRES_AT_KEY] = expires_at


def clear_session() -> None:
    for key in (
        SESSION_TOKEN_KEY,
        SESSION_USER_KEY,
        SESSION_EXPIRES_AT_KEY,
        "selected_model",
        "hf_models_cache",
        "deployment_result",
        "pending_action",
        "last_auth_error",
        "_request_nonce",
    ):
        st.session_state.pop(key, None)
    st.session_state["is_authenticated"] = False
