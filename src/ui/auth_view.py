import streamlit as st

from src import config
from src.hf_client import HFClient


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

    st.info("Connect your Hugging Face account to get started.")
    token_input = st.text_input("Hugging Face Access Token", type="password")

    if st.button("Connect"):
        if not token_input.strip():
            st.error("Please enter a token.")
        else:
            try:
                client = HFClient(token_input.strip())
                if client.is_valid_token():
                    config.save_hf_token(token_input.strip())
                    on_connect_change(True)
                    st.success(f"Connected as **{client.get_username()}**")
                    st.rerun()
                else:
                    st.error("Invalid token. Please check and try again.")
            except Exception as exc:
                st.error(f"Connection error: {exc}")

    return False
