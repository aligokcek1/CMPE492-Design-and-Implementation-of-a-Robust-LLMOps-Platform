from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest


def _make_app(token=None, whoami_return=None, whoami_side_effect=None,
              client_id=None, client_secret=None):
    at = AppTest.from_file("src/app.py")
    api_mock = MagicMock()
    if whoami_side_effect:
        api_mock.whoami.side_effect = whoami_side_effect
    else:
        api_mock.whoami.return_value = whoami_return or {"name": "testuser"}

    patches = [
        patch("src.config.get_hf_token", return_value=token),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=[]),
        patch("src.hf_client.HfApi", return_value=api_mock),
        patch("src.config.get_oauth_client_id", return_value=client_id or "test_client"),
        patch("src.config.get_oauth_client_secret", return_value=client_secret or "test_secret"),
    ]
    return at, patches


# ---------------------------------------------------------------------------
# Legacy: connected / disconnected states still work (regression, FR-009)
# ---------------------------------------------------------------------------


def test_auth_view_shows_connected_when_valid_token():
    at, patches = _make_app(token="valid_token")
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        at.run()
    assert not at.exception
    all_text = " ".join(str(e) for e in list(at.success) + list(at.info) + list(at.markdown))
    assert "testuser" in all_text or len(at.success) > 0


def test_auth_view_shows_error_on_invalid_token():
    at, patches = _make_app(token="bad_token", whoami_side_effect=Exception("Unauthorized"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        at.run()
    assert not at.exception


# ---------------------------------------------------------------------------
# T007: OAuth login button visible when unauthenticated (FR-001)
# ---------------------------------------------------------------------------


def test_auth_view_shows_login_button_when_no_token():
    """FR-001: A 'Login with Hugging Face' button must appear when unauthenticated."""
    at, patches = _make_app(token=None)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        at.run()
    assert not at.exception
    all_labels = [str(b) for b in at.button]
    assert any("Hugging Face" in label or "Login" in label for label in all_labels), (
        f"Expected a 'Login with Hugging Face' button. Found buttons: {all_labels}"
    )


def test_auth_view_no_manual_token_input_when_no_token():
    """SC-003: Manual token text_input must no longer be the primary UI element."""
    at, patches = _make_app(token=None)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        at.run()
    assert not at.exception
    # The old manual-token text_input should be gone
    token_inputs = [t for t in at.text_input if "token" in str(t).lower()]
    assert len(token_inputs) == 0, (
        f"Manual token input should be removed, but found: {token_inputs}"
    )
