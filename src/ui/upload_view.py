import streamlit as st

from src import config
from src.cache import ModelCache
from src.hf_client import HFClient

MAX_MB = 500


def render():
    """Render the Model Upload UI."""
    st.header("Upload Model")

    token = config.get_hf_token()
    if not token:
        st.error("Not connected. Please connect your Hugging Face account first.")
        return

    client = HFClient(token)
    cache = ModelCache()

    source = st.radio("Select model source", ["Local PC", "Public Hugging Face Repo"])

    if source == "Local PC":
        _render_local_upload(client, cache)
    else:
        _render_public_repo(client, cache)


def _render_local_upload(client: HFClient, cache: ModelCache):
    uploaded_file = st.file_uploader("Choose a model file")
    model_name = st.text_input("Model name (used for HF repo naming)")

    if st.button("Upload"):
        if not uploaded_file:
            st.error("Please select a file to upload.")
            return
        if not model_name.strip():
            st.error("Please enter a model name.")
            return

        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_MB:
            st.error(f"File is {file_size_mb:.1f} MB, which exceeds the {MAX_MB} MB limit.")
            return

        with st.spinner("Uploading to Hugging Face…"):
            try:
                hf_repo_id = client.upload_local_file(
                    uploaded_file, uploaded_file.name, model_name.strip()
                )
                cache.add_model(
                    name=model_name.strip(),
                    source_type="LOCAL_PC",
                    hf_repo_id=hf_repo_id,
                )
                st.success(f"Model uploaded successfully: `{hf_repo_id}`")
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Upload failed: {exc}")


def _render_public_repo(client: HFClient, cache: ModelCache):
    repo_id = st.text_input("Public HF Repository ID (e.g., `username/model-name`)")
    model_name = st.text_input("Friendly name for this model")

    if st.button("Add Reference"):
        if not repo_id.strip():
            st.error("Please enter a repository ID.")
            return
        if not model_name.strip():
            st.error("Please enter a model name.")
            return

        with st.spinner("Verifying repository…"):
            try:
                if client.verify_public_repo(repo_id.strip()):
                    cache.add_model(
                        name=model_name.strip(),
                        source_type="PUBLIC_HF_REPO",
                        hf_repo_id=repo_id.strip(),
                    )
                    st.success(f"Model reference added: `{repo_id.strip()}`")
                else:
                    st.error(
                        f"Repository `{repo_id.strip()}` is not accessible or does not exist."
                    )
            except Exception as exc:
                st.error(f"Verification failed: {exc}")
