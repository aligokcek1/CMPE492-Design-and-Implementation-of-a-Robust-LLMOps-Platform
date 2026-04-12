import sys
import os
import pytest
import streamlit as st

# Add frontend/ to sys.path so `src.*` imports work from any pytest invocation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def reset_streamlit_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()
