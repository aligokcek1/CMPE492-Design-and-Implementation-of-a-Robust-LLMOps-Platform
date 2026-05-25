# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026, Ali GÖKÇEK
"""LLMOps Platform Streamlit application entry point."""

import sys
import os

# Ensure the frontend/ directory is on sys.path so `src.*` imports resolve
# regardless of whether the script is launched via `streamlit run src/app.py`
# (which puts frontend/src/ on the path) or via pytest (which puts frontend/ on it).
_frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _frontend_dir not in sys.path:
    sys.path.insert(0, _frontend_dir)

import streamlit as st  # noqa: E402

from src.components.auth import render_login  # noqa: E402
from src.components.upload import render_upload_section, render_model_selector  # noqa: E402
from src.components.deploy import render_public_repo_deploy_section  # noqa: E402
from src.components.deployments_list import render_deployments_list  # noqa: E402
from src.components.sidebar import render_sidebar  # noqa: E402
from src.services.api_client import (  # noqa: E402
    APIError,
    get_gcp_credentials_status,
    get_lightning_credentials_status,
    get_session_status,
)
from src.services.session_client import (  # noqa: E402
    clear_session,
    get_persisted_session_token,
    get_session_token,
    set_session,
    sync_session_cookie,
)

st.set_page_config(
    page_title="LLMOps Platform",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def _is_authenticated() -> bool:
    return bool(get_session_token())


def _try_restore_session() -> None:
    if st.session_state.get("_session_checked"):
        return
    st.session_state["_session_checked"] = True
    token = get_session_token()
    if not token:
        token = get_persisted_session_token()
        if token:
            st.session_state["session_token"] = token
    if not token:
        return
    try:
        status = get_session_status(token)
        set_session(
            session_token=status["session_token"],
            username=status["username"],
            expires_at=status.get("expires_at"),
        )
    except APIError:
        clear_session()
    except Exception:
        clear_session()


def _render_credentials_invalid_banner() -> None:
    """Persistent warning for invalid GCP or Lightning AI credentials."""
    token = get_session_token()
    if not token:
        return
    try:
        gcp_status = get_gcp_credentials_status(token)
        if gcp_status.get("configured") and gcp_status.get("validation_status") == "invalid":
            st.warning(
                "**GCP credentials are invalid.** New CPU deployments and deletions are "
                "blocked until you update them under **Settings → GCP Credentials** in "
                "the sidebar. Running deployments are unaffected."
            )
    except Exception:
        pass
    try:
        lai_status = get_lightning_credentials_status(token)
        if lai_status.get("configured") and lai_status.get("validation_status") == "invalid":
            st.warning(
                "**Lightning AI API key is invalid.** New GPU deployments are blocked "
                "until you update it under **Settings → Lightning AI** in the sidebar."
            )
    except Exception:
        pass


def main() -> None:
    _try_restore_session()
    sync_session_cookie()
    render_sidebar()

    if not _is_authenticated():
        render_login()
        return

    if st.session_state.pop("reauth_completed", False):
        pending = st.session_state.pop("pending_action", None)
        if pending:
            st.success(
                "Re-authentication successful. You can continue: "
                f"`{pending.get('type', 'previous action')}`."
            )

    st.title("LLMOps Platform")
    st.markdown(
        "Upload or select a model, deploy to cloud infrastructure, and monitor "
        "running deployments from the tabs below."
    )

    _render_credentials_invalid_banner()

    tab_deployments, tab_upload, tab_select, tab_deploy = st.tabs(
        [
            "Deployments",
            "Upload Model",
            "Select Model",
            "Deploy",
        ]
    )

    with tab_deployments:
        try:
            render_deployments_list()
        except Exception as exc:
            st.error(f"An unexpected error occurred in the deployments section: {exc}")

    with tab_upload:
        try:
            render_upload_section()
        except Exception as exc:
            st.error(f"An unexpected error occurred in the upload section: {exc}")

    with tab_select:
        try:
            render_model_selector()
        except Exception as exc:
            st.error(f"An unexpected error occurred in the model selection section: {exc}")

    with tab_deploy:
        try:
            render_public_repo_deploy_section()
        except Exception as exc:
            st.error(f"An unexpected error occurred in the deploy section: {exc}")


if __name__ == "__main__":
    main()
