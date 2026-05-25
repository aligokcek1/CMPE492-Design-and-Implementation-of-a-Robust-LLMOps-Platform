import sys
import os
from unittest.mock import patch

import pytest
import streamlit as st

from tests.helpers.api_mocks import make_get_side_effect

# Add frontend/ to sys.path so `src.*` imports work from any pytest invocation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def reset_streamlit_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


@pytest.fixture(autouse=True)
def patch_api_get_defaults(request):
    """Prevent integration tests from hitting a real backend on sidebar/tab GETs."""
    if request.node.get_closest_marker("no_api_patch"):
        yield
        return
    with patch(
        "src.services.api_client.requests.get",
        side_effect=make_get_side_effect(),
    ):
        yield
