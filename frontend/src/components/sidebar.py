"""Sidebar profile strip and Settings panel for cloud credentials."""

from __future__ import annotations

import streamlit as st

from src.components.gcp_credentials import render_gcp_credentials_section
from src.components.lightning_ai_credentials import render_lightning_ai_credentials_section
from src.services.api_client import logout
from src.services.session_client import clear_session, get_session_token


def _is_authenticated() -> bool:
    return bool(get_session_token())


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### LLMOps Platform")
        st.markdown("---")
        if _is_authenticated():
            username = st.session_state.get("hf_username", "Unknown")
            st.markdown(f"**Signed in as** {username}")
            if st.button("Sign Out", use_container_width=True, key="sidebar_sign_out"):
                token = get_session_token()
                if token:
                    try:
                        logout(token)
                    except Exception:
                        pass
                clear_session()
                st.rerun()
        else:
            st.info("Not authenticated.")

        if _is_authenticated():
            with st.expander("Settings", expanded=False):
                st.markdown("#### GCP Credentials")
                render_gcp_credentials_section()
                st.markdown("---")
                st.markdown("#### Lightning AI")
                render_lightning_ai_credentials_section()

        st.markdown("---")
        st.caption(
            "© 2026 Ali GÖKÇEK · Licensed under "
            "[BSD-2-Clause](https://opensource.org/license/bsd-2-clause)"
        )
