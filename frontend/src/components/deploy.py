import streamlit as st

from src.services.api_client import (
    APIError,
    create_deployment,
    fetch_public_model_info,
)
from src.services.session_client import get_session_token


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def render_public_repo_deploy_section() -> None:
    """Render UI for real GKE CPU / Lightning AI GPU deployment of any HF model."""
    st.subheader("Deploy to Cloud")

    session_token = get_session_token()

    shortcut = st.session_state.pop("shortcut_deploy_model", None)
    if shortcut:
        st.success(f"Ready to deploy **{shortcut}**.")

    repo_id = st.text_input(
        "Model Repository ID",
        value=shortcut or "",
        placeholder="owner/repo-name",
        help=(
            "HuggingFace repository identifier, e.g. `Qwen/Qwen3-1.7B` or `your-username/my-model`. "
            "Works for public, private, and gated repositories — your HuggingFace token is used automatically."
        ),
        key="public_repo_id_input",
    )

    if st.button("Fetch Repository Info", key="btn_fetch_public_repo"):
        if not repo_id or "/" not in repo_id:
            st.error("Invalid format. Please use owner/repo-name (e.g. Qwen/Qwen3-1.7B).")
        else:
            with st.spinner("Fetching repository metadata…"):
                try:
                    info = fetch_public_model_info(session_token, repo_id)
                    st.session_state["public_repo_info"] = info
                except APIError as exc:
                    st.session_state.pop("public_repo_info", None)
                    if exc.status_code == 401:
                        st.session_state["last_auth_error"] = (
                            "Session expired. Please sign in again."
                        )
                        st.session_state["pending_action"] = {
                            "type": "fetch_public_info",
                            "repo_id": repo_id,
                        }
                        st.error("Session expired. Please sign in again.")
                        return
                    if exc.status_code == 404:
                        st.error("Repository not found. Check the repository ID and try again.")
                    elif exc.status_code == 403:
                        st.error(
                            "Access denied for this repository. "
                            "If it is gated or private, ensure your HuggingFace token has read access."
                        )
                    elif exc.status_code == 400:
                        st.error("Invalid repository ID format. Use owner/repo-name.")
                    else:
                        st.error(f"Failed to fetch repository info: {exc.detail}")
                except Exception as exc:
                    st.session_state.pop("public_repo_info", None)
                    st.error(f"Unexpected error: {exc}")

    info = st.session_state.get("public_repo_info")
    if info:
        st.info(
            f"**{info['repo_id']}** by **{info['author']}**\n\n"
            f"{info.get('description') or 'No description available.'}\n\n"
            f"Files: {info['file_count']}  ·  Size: {_format_size(info.get('size_bytes'))}"
        )

        hardware_type = st.radio(
            "Hardware",
            options=["CPU", "GPU"],
            index=None,
            horizontal=True,
            key="public_repo_hardware_selector",
            help=(
                "**CPU** — deploys on GKE Autopilot via TGI (requires GCP credentials). "
                "**GPU** — deploys on Lightning AI managed cloud via vLLM "
                "(requires a Lightning AI API key from **Settings → Lightning AI** in the sidebar)."
            ),
        )

        deploy_disabled = hardware_type is None
        deploy_label = (
            "Deploy to GKE (CPU)"
            if hardware_type == "CPU"
            else "Deploy to Lightning AI (GPU)"
            if hardware_type == "GPU"
            else "Deploy"
        )
        deploy_btn = st.button(
            deploy_label,
            key="btn_pub_gke_deploy",
            type="primary",
            use_container_width=True,
            disabled=deploy_disabled,
        )
        if deploy_btn and hardware_type:
            _handle_real_deploy(
                session_token, info["repo_id"], hardware_type=hardware_type.lower(), force=False
            )

        dup_pending = st.session_state.get("_duplicate_confirm_for")
        if dup_pending == info["repo_id"] and hardware_type:
            st.warning(
                f"You already have a running deployment of **{info['repo_id']}**. "
                "Deploy another copy anyway?"
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(
                    "Yes, deploy another", key="btn_pub_confirm_dup", use_container_width=True
                ):
                    _handle_real_deploy(
                        session_token,
                        info["repo_id"],
                        hardware_type=hardware_type.lower(),
                        force=True,
                    )
            with col_no:
                if st.button("Cancel", key="btn_pub_cancel_dup", use_container_width=True):
                    st.session_state.pop("_duplicate_confirm_for", None)
                    st.rerun()


def _handle_real_deploy(
    session_token: str, hf_model_id: str, *, hardware_type: str, force: bool
) -> None:
    try:
        result = create_deployment(
            session_token, hf_model_id, hardware_type=hardware_type, force=force
        )
        st.session_state.pop("_duplicate_confirm_for", None)
        platform = "GKE (CPU)" if hardware_type == "cpu" else "Lightning AI (GPU)"
        st.success(
            f"Deployment accepted on **{platform}**. Status: **{result['status']}**. "
            f"Follow its progress in the **Deployments** tab. ID: `{result['id']}`"
        )
        st.session_state["last_deployment"] = result
    except APIError as exc:
        if exc.status_code == 409 and exc.code == "duplicate_model_requires_confirmation":
            st.session_state["_duplicate_confirm_for"] = hf_model_id
            st.rerun()
        elif exc.status_code == 409 and exc.code == "concurrent_deployment_limit":
            st.error(
                "You have reached the maximum of 3 concurrent deployments. "
                "Delete one first, then try again."
            )
        elif exc.status_code == 409 and exc.code in (
            "lightning_credentials_missing",
            "lightning_credentials_invalid",
        ):
            st.error(
                "Lightning AI API key is missing or invalid. "
                "Add or update it under **Settings → Lightning AI** in the sidebar."
            )
        elif exc.status_code == 409 and exc.code in ("credentials_missing", "credentials_invalid"):
            st.error(
                "GCP credentials are missing or invalid. Update them under "
                "**Settings → GCP Credentials** in the sidebar before CPU deployment."
            )
        elif exc.status_code == 400 and exc.code == "hf_hub_unreachable":
            st.error("HuggingFace Hub is currently unreachable. Please retry.")
        elif exc.status_code == 400 and exc.code == "model_access_denied":
            st.error(
                "Access denied for this repository. "
                "Ensure your HuggingFace token has read permission."
            )
        elif exc.status_code == 400 and exc.code == "unsupported_model":
            st.error(
                "This model type is not supported for deployment. "
                "Only text-generation / NLP models are supported in this version."
            )
        elif exc.status_code == 400 and exc.code == "model_not_found":
            st.error(f"Model not found on HuggingFace: {exc.detail}")
        elif exc.status_code == 401:
            st.error("Session expired. Please sign in again.")
        else:
            st.error(f"Deployment failed: {exc.detail}")
    except Exception as exc:
        st.error(f"Unexpected error during deployment: {exc}")
