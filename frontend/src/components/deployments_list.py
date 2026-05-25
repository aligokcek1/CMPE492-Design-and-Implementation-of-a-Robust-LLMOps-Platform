"""Deployments tab: fleet overview, dense rows, and detail disclosures."""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.components.deployment_details import render_deployment_details
from src.components.fleet_overview import render_fleet_overview
from src.services.api_client import (
    APIError,
    delete_deployment,
    dismiss_deployment,
    list_deployments,
)
from src.services.session_client import get_session_token
from src.ui.fleet_counts import compute_fleet_counts, filter_visible_deployments
from src.ui.status_display import render_status_badge


def _hardware_label(dep: dict[str, Any]) -> str:
    hw = dep.get("hardware_type", "cpu")
    return "CPU · GKE" if hw == "cpu" else "GPU · Lightning AI"


def _fetch_deployments() -> tuple[list[dict[str, Any]] | None, str | None]:
    """Return (deployments, error_message). error_message set on API failure."""
    token = get_session_token()
    if not token:
        return None, "Sign in to view deployments."
    try:
        return list_deployments(token), None
    except APIError as exc:
        return None, exc.detail or "Could not load deployments. Please try again."


def _render_single_deployment(dep: dict[str, Any]) -> None:
    dep_id = dep["id"]
    status = dep.get("status", "")
    hw = dep.get("hardware_type", "cpu")
    origin = " · **Uploaded**" if dep.get("model_origin") == "uploaded" else ""
    title = dep.get("hf_model_display_name") or dep["hf_model_id"]

    with st.container(border=True):
        header = st.columns([5, 2, 1])
        with header[0]:
            st.markdown(f"**{title}**{origin}")
            st.caption(f"`{dep['hf_model_id']}` · {_hardware_label(dep)}")
        with header[1]:
            render_status_badge(status)
        with header[2]:
            if status == "lost":
                if st.button("Dismiss", key=f"dismiss_{dep_id}", use_container_width=True):
                    _handle_dismiss(dep_id)
            elif status not in ("deleted",):
                if st.button(
                    "Delete",
                    key=f"delete_{dep_id}",
                    use_container_width=True,
                    disabled=status == "deleting",
                ):
                    st.session_state[f"_confirm_delete_{dep_id}"] = True
                    st.rerun()

        endpoint = dep.get("endpoint_url")
        if endpoint:
            st.markdown("**Endpoint**")
            st.code(endpoint, language=None)
        else:
            st.caption("Endpoint pending")

        if st.session_state.get(f"_confirm_delete_{dep_id}"):
            platform = "GCP project" if hw == "cpu" else "Lightning AI deployment"
            st.warning(
                f"Delete `{dep_id[:8]}` and tear down its {platform}? This cannot be undone."
            )
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button(
                    "Yes, delete",
                    key=f"delete_confirm_{dep_id}",
                    use_container_width=True,
                ):
                    _handle_delete(dep_id)
            with c_no:
                if st.button(
                    "Cancel",
                    key=f"delete_cancel_{dep_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(f"_confirm_delete_{dep_id}", None)
                    st.rerun()

        render_deployment_details(dep)


def _handle_delete(dep_id: str) -> None:
    token = get_session_token()
    try:
        delete_deployment(token, dep_id)
        st.success(f"Deletion of `{dep_id[:8]}` queued.")
    except APIError as exc:
        if exc.status_code == 409 and exc.code == "credentials_invalid":
            st.error(
                "GCP credentials are invalid. Update them under "
                "**Settings → GCP Credentials** in the sidebar."
            )
        else:
            st.error(f"Delete failed: {exc.detail}")
    finally:
        st.session_state.pop(f"_confirm_delete_{dep_id}", None)
        st.rerun()


def _handle_dismiss(dep_id: str) -> None:
    token = get_session_token()
    try:
        dismiss_deployment(token, dep_id)
        st.success("Lost deployment dismissed.")
    except APIError as exc:
        st.error(f"Dismiss failed: {exc.detail}")
    st.rerun()


def render_deployments_list() -> None:
    with st.spinner("Loading deployments…"):
        deployments, fetch_error = _fetch_deployments()

    if fetch_error:
        st.error(fetch_error)
        return

    if deployments is None:
        return

    visible = filter_visible_deployments(deployments)
    render_fleet_overview(compute_fleet_counts(visible))

    st.divider()

    st.markdown("#### Deployments")
    if not visible:
        st.info(
            "No deployments yet. Open the **Deploy** tab to launch a model from Hugging Face."
        )
        return

    st.caption(
        f"{len(visible)} deployment{'s' if len(visible) != 1 else ''} "
        f"({len(deployments)} total from API, deleted hidden)."
    )

    for dep in visible:
        _render_single_deployment(dep)


__all__ = ["render_deployments_list"]
