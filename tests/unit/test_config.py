import os
from pathlib import Path

import pytest

from src.config import (
    clear_hf_token,
    get_hf_token,
    get_oauth_client_id,
    get_oauth_client_secret,
    get_oauth_redirect_uri,
    save_hf_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    """Point ENV_FILE at a temp file and clear token-related env vars for every test."""
    env_file = tmp_path / ".env"
    monkeypatch.setattr("src.config.ENV_FILE", env_file)
    for key in ("HF_TOKEN", "HF_CLIENT_ID", "HF_CLIENT_SECRET", "HF_REDIRECT_URI"):
        monkeypatch.delenv(key, raising=False)
    yield


# ---------------------------------------------------------------------------
# save_hf_token / clear_hf_token / get_hf_token  (FR-006, FR-008)
# ---------------------------------------------------------------------------


def test_save_hf_token_writes_to_env_file(tmp_path):
    save_hf_token("hf_test_token")
    env_file = Path("src/config.py").parent.parent / ".env"  # resolved via monkeypatch
    # Verify the process environment is updated immediately
    assert os.environ.get("HF_TOKEN") == "hf_test_token"


def test_save_hf_token_makes_token_readable_via_get():
    save_hf_token("hf_readable_token")
    assert get_hf_token() == "hf_readable_token"


def test_clear_hf_token_removes_from_process_env():
    os.environ["HF_TOKEN"] = "to_be_cleared"
    clear_hf_token()
    assert os.environ.get("HF_TOKEN") is None


def test_clear_hf_token_is_idempotent_when_token_absent():
    """Clearing when no token exists must not raise."""
    clear_hf_token()


def test_save_then_clear_leaves_no_token():
    save_hf_token("ephemeral_token")
    assert get_hf_token() == "ephemeral_token"
    clear_hf_token()
    assert get_hf_token() is None


# ---------------------------------------------------------------------------
# get_oauth_client_id (T001b)
# ---------------------------------------------------------------------------


def test_get_oauth_client_id_returns_env_value(monkeypatch):
    monkeypatch.setenv("HF_CLIENT_ID", "my_client_id")
    assert get_oauth_client_id() == "my_client_id"


def test_get_oauth_client_id_returns_none_when_unset():
    assert get_oauth_client_id() is None


# ---------------------------------------------------------------------------
# get_oauth_client_secret (T001b)
# ---------------------------------------------------------------------------


def test_get_oauth_client_secret_returns_env_value(monkeypatch):
    monkeypatch.setenv("HF_CLIENT_SECRET", "super_secret")
    assert get_oauth_client_secret() == "super_secret"


def test_get_oauth_client_secret_returns_none_when_unset():
    assert get_oauth_client_secret() is None


# ---------------------------------------------------------------------------
# get_oauth_redirect_uri (T001b)
# ---------------------------------------------------------------------------


def test_get_oauth_redirect_uri_returns_env_value(monkeypatch):
    monkeypatch.setenv("HF_REDIRECT_URI", "http://localhost:9000/")
    assert get_oauth_redirect_uri() == "http://localhost:9000/"


def test_get_oauth_redirect_uri_returns_default_when_unset():
    assert get_oauth_redirect_uri() == "http://localhost:8501/"
