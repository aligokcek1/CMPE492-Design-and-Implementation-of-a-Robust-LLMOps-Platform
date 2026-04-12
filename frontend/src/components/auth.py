import streamlit as st
from src.services.api_client import verify_token, APIError
from src.services.session_client import set_session


def render_login() -> None:
    """Render the Hugging Face login / token entry form."""
    st.header("Sign in with Hugging Face")
    last_auth_error = st.session_state.get("last_auth_error")
    pending_action = st.session_state.get("pending_action")
    if last_auth_error:
        st.warning(last_auth_error)
    if pending_action:
        st.info(
            "After sign in, you can continue your previous action: "
            f"`{pending_action.get('type', 'unknown')}`."
        )
    st.markdown(
        "Enter a Hugging Face **write-access** token to authenticate. "
        "You can generate one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)."
    )

    with st.form("hf_login_form", clear_on_submit=False):
        token = st.text_input(
            "Access Token",
            type="password",
            placeholder="hf_...",
            help="Your Hugging Face token with write permissions.",
        )
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not token.strip():
            st.error("Please enter a Hugging Face access token.")
            return

        with st.spinner("Verifying token…"):
            try:
                result = verify_token(token.strip())
                set_session(
                    session_token=result["session_token"],
                    username=result["username"],
                    expires_at=result.get("expires_at"),
                )
                st.session_state.pop("last_auth_error", None)
                st.session_state["reauth_completed"] = True
                st.success(f"Authenticated as **{result['username']}**")
                st.rerun()
            except APIError as exc:
                if exc.status_code == 401:
                    st.error("Invalid token. Please check your Hugging Face access token.")
                else:
                    st.error(f"Authentication failed: {exc.detail}")
            except Exception as exc:
                st.error(f"Could not reach the backend: {exc}")
