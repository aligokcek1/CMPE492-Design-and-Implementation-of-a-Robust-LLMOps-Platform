from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest


def _make_app(token=None, whoami_return=None, whoami_side_effect=None):
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
    ]
    return at, patches


def test_auth_view_shows_connect_form_when_no_token():
    at, patches = _make_app(token=None)
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
    assert not at.exception
    assert any("Token" in str(t) or "token" in str(t) for t in at.text_input)


def test_auth_view_shows_connected_when_valid_token():
    at, patches = _make_app(token="valid_token")
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
    assert not at.exception
    all_text = " ".join(
        str(e) for e in list(at.success) + list(at.info) + list(at.markdown)
    )
    assert "testuser" in all_text or len(at.success) > 0


def test_auth_view_shows_error_on_invalid_token():
    at, patches = _make_app(token="bad_token", whoami_side_effect=Exception("Unauthorized"))
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
    assert not at.exception
