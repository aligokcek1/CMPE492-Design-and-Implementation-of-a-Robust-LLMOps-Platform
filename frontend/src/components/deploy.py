import streamlit as st
from src.services.api_client import mock_deploy, fetch_public_model_info, APIError
from src.services.session_client import get_session_token
import uuid


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def render_deployment_section() -> None:
    """Render the GCP deployment configuration and mock deployment UI."""
    st.subheader("Deploy to GCP (Simulated)")

    selected_model = st.session_state.get("selected_model", "")
    if not selected_model:
        st.warning("No model selected. Please upload or select a model first.")
        return

    st.markdown(f"**Model to deploy**: `{selected_model}`")

    col1, col2 = st.columns(2)
    with col1:
        cpu_selected = st.button(
            "🖥️ CPU",
            key="btn_cpu",
            use_container_width=True,
            help="Deploy on CPU infrastructure",
        )
    with col2:
        gpu_selected = st.button(
            "⚡ GPU",
            key="btn_gpu",
            use_container_width=True,
            help="Deploy on GPU infrastructure",
        )

    resource_type = None
    if cpu_selected:
        resource_type = "CPU"
    elif gpu_selected:
        resource_type = "GPU"

    if resource_type:
        session_token = get_session_token()
        deploy_key = st.session_state.get("_deploy_request_nonce")
        if not deploy_key:
            deploy_key = str(uuid.uuid4())
            st.session_state["_deploy_request_nonce"] = deploy_key
        with st.spinner(f"Simulating {resource_type} deployment…"):
            try:
                result = mock_deploy(
                    session_token,
                    selected_model,
                    resource_type,
                    idempotency_key=f"deploy:{deploy_key}",
                )
                st.success(f"**{result['status'].upper()}**: {result['message']}")
                st.balloons()
                st.session_state["deployment_result"] = result
                st.session_state.pop("_deploy_request_nonce", None)
            except APIError as exc:
                if exc.status_code == 401:
                    st.session_state["last_auth_error"] = "Session expired. Please sign in again."
                    st.session_state["pending_action"] = {
                        "type": "deploy",
                        "model_repository": selected_model,
                        "resource_type": resource_type,
                    }
                    st.error("Session expired. Please sign in again.")
                    return
                st.error(f"Deployment failed: {exc.detail}")
            except Exception as exc:
                st.error(f"Unexpected error during deployment: {exc}")

    if "deployment_result" in st.session_state:
        with st.expander("Last Deployment Result", expanded=False):
            r = st.session_state["deployment_result"]
            st.json(r)


def render_public_repo_deploy_section() -> None:
    """Render UI for fetching public repo metadata and triggering mock deployment."""
    st.subheader("Deploy a Public Repository")

    session_token = get_session_token()
    repo_id = st.text_input(
        "Public Repository ID",
        placeholder="owner/repo-name",
        help="Full Hugging Face repository identifier, e.g. google-bert/bert-base-uncased",
        key="public_repo_id_input",
    )

    if st.button("Fetch Repository Info", key="btn_fetch_public_repo"):
        if not repo_id or "/" not in repo_id:
            st.error("Invalid format. Please use owner/repo-name (e.g. google-bert/bert-base-uncased).")
        else:
            with st.spinner("Fetching repository metadata…"):
                try:
                    info = fetch_public_model_info(session_token, repo_id)
                    st.session_state["public_repo_info"] = info
                except APIError as exc:
                    st.session_state.pop("public_repo_info", None)
                    if exc.status_code == 401:
                        st.session_state["last_auth_error"] = "Session expired. Please sign in again."
                        st.session_state["pending_action"] = {
                            "type": "fetch_public_info",
                            "repo_id": repo_id,
                        }
                        st.error("Session expired. Please sign in again.")
                        return
                    if exc.status_code == 404:
                        st.error("Repository not found. Check the repository ID and try again.")
                    elif exc.status_code == 403:
                        st.error("Repository is private. Only public repositories can be deployed this way.")
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

        col1, col2 = st.columns(2)
        with col1:
            pub_cpu = st.button(
                "🖥️ CPU",
                key="btn_pub_cpu",
                use_container_width=True,
            )
        with col2:
            pub_gpu = st.button(
                "⚡ GPU",
                key="btn_pub_gpu",
                use_container_width=True,
            )

        pub_resource = None
        if pub_cpu:
            pub_resource = "CPU"
        elif pub_gpu:
            pub_resource = "GPU"

        if pub_resource:
            deploy_key = st.session_state.get("_public_deploy_request_nonce")
            if not deploy_key:
                deploy_key = str(uuid.uuid4())
                st.session_state["_public_deploy_request_nonce"] = deploy_key
            with st.spinner(f"Deploying {info['repo_id']} on {pub_resource}…"):
                try:
                    result = mock_deploy(
                        session_token,
                        info["repo_id"],
                        pub_resource,
                        idempotency_key=f"deploy:{deploy_key}",
                    )
                    st.success(f"**{result['status'].upper()}**: {result['message']}")
                    st.balloons()
                    st.session_state.pop("_public_deploy_request_nonce", None)
                except APIError as exc:
                    if exc.status_code == 401:
                        st.session_state["last_auth_error"] = "Session expired. Please sign in again."
                        st.session_state["pending_action"] = {
                            "type": "deploy_public",
                            "model_repository": info["repo_id"],
                            "resource_type": pub_resource,
                        }
                        st.error("Session expired. Please sign in again.")
                        return
                    st.error(f"Deployment failed: {exc.detail}")
                except Exception as exc:
                    st.error(f"Unexpected error during deployment: {exc}")
