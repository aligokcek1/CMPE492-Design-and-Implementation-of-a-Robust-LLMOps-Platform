"""Streamlit component for the ⚡ Lightning AI credentials tab."""
from __future__ import annotations

import streamlit as st

from src.services.api_client import (
    APIError,
    delete_lightning_credentials,
    get_lightning_credentials_status,
    save_lightning_credentials,
)
from src.services.session_client import get_session_token


def _fetch_status() -> dict | None:
    token = get_session_token()
    if not token:
        return None
    try:
        return get_lightning_credentials_status(token)
    except APIError as exc:
        st.error(f"Failed to load Lightning AI credential status: {exc.detail}")
        return None


def _render_status_panel(status: dict) -> None:
    if not status.get("configured"):
        st.info(
            "No Lightning AI API key configured yet. Save your API key to enable GPU deployments."
        )
        return

    validation = status.get("validation_status") or "valid"
    if validation == "invalid":
        st.warning(
            "Your Lightning AI API key is currently **invalid** — it may have been revoked or expired. "
            "New GPU deployments are blocked until you update it."
        )
    else:
        st.success("Lightning AI API key is configured and **valid**.")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Validation status**")
        st.code(validation, language=None)
    with cols[1]:
        st.markdown("**Last validated**")
        st.code(status.get("last_validated_at") or "—", language=None)

    if status.get("validation_error_message"):
        with st.expander("Validation error details"):
            st.code(status["validation_error_message"], language=None)


def _render_save_form() -> None:
    with st.form("lightning_ai_credentials_form", clear_on_submit=True):
        st.markdown(
            "Paste your **Lightning AI User ID** and **API key** from your "
            "[Lightning AI profile](https://lightning.ai/settings). "
            "The API key is encrypted at rest and never returned by the backend."
        )
        lightning_user_id = st.text_input(
            "Lightning AI User ID (LIGHTNING_USER_ID)",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            key="lightning_ai_user_id_input",
        )
        api_key = st.text_input(
            "Lightning AI API key (LIGHTNING_API_KEY)",
            type="password",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            key="lightning_ai_key_input",
        )
        submitted = st.form_submit_button(
            "Save and validate", type="primary", use_container_width=True
        )

    if not submitted:
        return

    token = get_session_token()
    if not token:
        st.error("You must be signed in to save credentials.")
        return
    if not lightning_user_id.strip():
        st.error("Lightning AI User ID cannot be empty.")
        return
    if not api_key.strip():
        st.error("API key cannot be empty.")
        return

    try:
        new_status = save_lightning_credentials(token, lightning_user_id.strip(), api_key.strip())
    except APIError as exc:
        st.error(f"Credential validation failed: {exc.detail}")
        return

    st.success("Lightning AI API key saved and validated.")
    st.session_state["lightning_ai_credential_status"] = new_status
    st.rerun()


def render_lightning_ai_credentials_section() -> None:
    st.subheader("Lightning AI credentials")
    status = _fetch_status()
    if status is None:
        return

    _render_status_panel(status)
    st.divider()

    if status.get("configured"):
        cols = st.columns(2)
        with cols[0]:
            if st.button("Replace API key", use_container_width=True):
                st.session_state["_lightning_ai_show_form"] = True
        with cols[1]:
            if st.button("Delete API key", type="secondary", use_container_width=True):
                token = get_session_token()
                try:
                    delete_lightning_credentials(token)
                    st.success("Lightning AI API key deleted.")
                    st.session_state.pop("_lightning_ai_show_form", None)
                    st.rerun()
                except APIError as exc:
                    st.error(f"Delete failed: {exc.detail}")

        if st.session_state.get("_lightning_ai_show_form"):
            _render_save_form()
    else:
        _render_save_form()


__all__ = ["render_lightning_ai_credentials_section"]
