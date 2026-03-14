"""
Integration tests for OAuth callback handling in src/app.py (T008).

These tests simulate Streamlit loading with ?code=...&state=... query params,
verifying the full callback flow: token exchange → save → connected state.
"""

from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest


def _make_callback_app(code="auth_code_123", state="saved_state_abc",
                       saved_session_state=None, token_response=None,
                       fetch_side_effect=None):
    """Build an AppTest that loads with OAuth callback query params set."""
    at = AppTest.from_file("src/app.py")

    if saved_session_state is not None:
        at.session_state["oauth_state"] = saved_session_state

    api_mock = MagicMock()
    api_mock.whoami.return_value = {"name": "oauthuser"}

    mock_token = token_response or {"access_token": "hf_oauth_token_xyz"}

    oauth_patches = [
        patch("src.config.get_hf_token", return_value=None),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=[]),
        patch("src.hf_client.HfApi", return_value=api_mock),
        patch("src.config.get_oauth_client_id", return_value="test_client"),
        patch("src.config.get_oauth_client_secret", return_value="test_secret"),
        patch("src.config.save_hf_token"),
    ]

    if fetch_side_effect:
        oauth_patches.append(
            patch("src.oauth.HFOAuthService.fetch_token", side_effect=fetch_side_effect)
        )
    else:
        oauth_patches.append(
            patch("src.oauth.HFOAuthService.fetch_token", return_value=mock_token)
        )

    at.query_params["code"] = code
    at.query_params["state"] = state

    return at, oauth_patches


# ---------------------------------------------------------------------------
# Successful callback flow (FR-003, FR-004, FR-006, SC-002)
# ---------------------------------------------------------------------------


def test_successful_callback_saves_token():
    """FR-006: A successful callback must result in save_hf_token being called."""
    at = AppTest.from_file("src/app.py")
    at.session_state["oauth_state"] = "correct_state"
    at.query_params["code"] = "auth_code_123"
    at.query_params["state"] = "correct_state"

    api_mock = MagicMock()
    api_mock.whoami.return_value = {"name": "oauthuser"}
    mock_token = {"access_token": "hf_oauth_token_xyz"}

    with (
        patch("src.config.get_hf_token", return_value=None),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=[]),
        patch("src.hf_client.HfApi", return_value=api_mock),
        patch("src.config.get_oauth_client_id", return_value="test_client"),
        patch("src.config.get_oauth_client_secret", return_value="test_secret"),
        patch("src.config.save_hf_token") as mock_save,
        patch("src.oauth.HFOAuthService.fetch_token", return_value=mock_token),
    ):
        at.run()

    assert not at.exception
    mock_save.assert_called_once_with("hf_oauth_token_xyz")


def test_successful_callback_shows_connected_state():
    """SC-002: After a successful callback, is_connected must be True in session_state."""
    at = AppTest.from_file("src/app.py")
    at.session_state["oauth_state"] = "correct_state"
    at.query_params["code"] = "auth_code_123"
    at.query_params["state"] = "correct_state"

    api_mock = MagicMock()
    api_mock.whoami.return_value = {"name": "oauthuser"}
    mock_token = {"access_token": "hf_oauth_token_xyz"}

    with (
        patch("src.config.get_hf_token", return_value=None),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=[]),
        patch("src.hf_client.HfApi", return_value=api_mock),
        patch("src.config.get_oauth_client_id", return_value="test_client"),
        patch("src.config.get_oauth_client_secret", return_value="test_secret"),
        patch("src.config.save_hf_token"),
        patch("src.oauth.HFOAuthService.fetch_token", return_value=mock_token),
    ):
        at.run()

    assert not at.exception
    # SC-002: session_state must reflect the connected state after a successful callback
    assert at.session_state["is_connected"] is True


# ---------------------------------------------------------------------------
# Error / denial flows (FR-005, Edge Cases)
# ---------------------------------------------------------------------------


def test_callback_with_state_mismatch_shows_error():
    """FR-005 / Edge Case: State mismatch (CSRF) must produce a user-visible error."""
    at, patches = _make_callback_app(
        state="tampered_state",
        saved_session_state="original_state",
        fetch_side_effect=ValueError("OAuth state mismatch"),
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        at.run()
    assert not at.exception
    all_text = " ".join(str(e) for e in list(at.error) + list(at.warning))
    assert len(at.error) > 0 or len(at.warning) > 0, (
        "A state mismatch must surface as a visible error in the UI."
    )


def test_no_callback_params_shows_login_button():
    """App loaded without query params should show the login button, not attempt exchange."""
    at = AppTest.from_file("src/app.py")
    api_mock = MagicMock()
    api_mock.whoami.return_value = {"name": "testuser"}
    with (
        patch("src.config.get_hf_token", return_value=None),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=[]),
        patch("src.hf_client.HfApi", return_value=api_mock),
        patch("src.config.get_oauth_client_id", return_value="test_client"),
        patch("src.config.get_oauth_client_secret", return_value="test_secret"),
    ):
        at.run()
    assert not at.exception
    all_labels = [str(b) for b in at.button]
    assert any("Login" in label or "Hugging Face" in label for label in all_labels)
