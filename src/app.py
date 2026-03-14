import sys
from pathlib import Path

# Ensure the project root is on sys.path when launched via `streamlit run src/app.py`
_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

from src import config
from src.cache import ModelCache
from src.hf_client import HFClient
from src.ui import auth_view, deploy_view, upload_view

st.set_page_config(page_title="LLM Inference App", layout="wide")

config.load_config()

_cache = ModelCache()
_cache.init_db()


def _on_connect_change(connected: bool):
    st.session_state["is_connected"] = connected
    if connected:
        _sync_cache()


def _sync_cache():
    """Sync local model registry against actual HF repos (FR-012)."""
    token = config.get_hf_token()
    if not token:
        return
    try:
        client = HFClient(token)
        user_repos = client.list_user_repos()
        _cache.sync_with_hf(user_repos)
    except Exception:
        pass


if "is_connected" not in st.session_state:
    token = config.get_hf_token()
    st.session_state["is_connected"] = bool(token)
    if st.session_state["is_connected"]:
        _sync_cache()

st.title("LLM Inference App")
st.sidebar.title("Navigation")

_pages = ["Account", "Upload Model", "Deploy & Inference"]
if not st.session_state.get("is_connected"):
    _pages = ["Account"]

_page = st.sidebar.radio("Go to", _pages)

if _page == "Account":
    auth_view.render(_on_connect_change)
elif _page == "Upload Model":
    upload_view.render()
elif _page == "Deploy & Inference":
    deploy_view.render()
