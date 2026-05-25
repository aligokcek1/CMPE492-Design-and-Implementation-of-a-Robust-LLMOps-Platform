"""Per-deployment detail disclosure (metrics, inference, diagnostics)."""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.components.deployment_metrics import render_deployment_metrics_panel
from src.services.api_client import APIError, run_inference
from src.services.session_client import get_session_token


def _render_inference_panel(deployment_id: str, endpoint_url: str | None) -> None:
    if not endpoint_url:
        return

    st.markdown("**Run inference**")
    with st.form(f"inference_form_{deployment_id}", clear_on_submit=False):
        prompt = st.text_area(
            "Prompt",
            height=120,
            key=f"prompt_{deployment_id}",
            placeholder="Write a short haiku about serverless inference.",
        )
        max_tokens = st.number_input(
            "Max tokens",
            min_value=1,
            max_value=4096,
            value=256,
            key=f"maxtok_{deployment_id}",
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            key=f"temp_{deployment_id}",
        )
        submitted = st.form_submit_button("Send")

    if submitted:
        token = get_session_token()
        if not prompt.strip():
            st.warning("Prompt is empty.")
            return
        with st.spinner("Waiting for model (up to 120s)…"):
            try:
                result = run_inference(
                    token,
                    deployment_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=int(max_tokens),
                    temperature=float(temperature),
                )
            except APIError as exc:
                if exc.status_code == 504:
                    st.error(
                        "Model did not respond within 120 seconds. "
                        "Click Send again to retry."
                    )
                elif exc.status_code == 409:
                    st.error(f"Deployment is not running: {exc.detail}")
                else:
                    st.error(f"Inference failed: {exc.detail}")
                return
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")
                return

        choices = result.get("choices", [])
        if choices:
            msg = choices[0].get("message", {}).get("content", "")
            st.success("Response:")
            st.markdown(msg)
        else:
            st.json(result)


def render_deployment_details(dep: dict[str, Any]) -> None:
    """Collapsed-by-default disclosure for verbose per-deployment content (FR-005)."""
    dep_id = dep["id"]
    status = dep.get("status", "")
    hw = dep.get("hardware_type", "cpu")
    label = dep.get("hf_model_display_name") or dep.get("hf_model_id", dep_id[:8])

    with st.expander(f"Details — {label}", expanded=False):
        if dep.get("status_message"):
            st.markdown("**Status**")
            st.info(dep["status_message"])

        if status == "running":
            render_deployment_metrics_panel(dep_id, hw, inline=True)
            _render_inference_panel(dep_id, dep.get("endpoint_url"))
        elif status in ("deploying", "queued", "deleting", "failed", "lost"):
            if status in ("failed", "lost") and dep.get("status_message"):
                st.error(dep["status_message"])


__all__ = ["render_deployment_details"]
