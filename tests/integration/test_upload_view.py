from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def _make_connected_app(models=None):
    at = AppTest.from_file("src/app.py")
    api_mock = MagicMock()
    api_mock.whoami.return_value = {"name": "testuser"}

    patches = [
        patch("src.config.get_hf_token", return_value="valid_token"),
        patch("src.cache.ModelCache.init_db"),
        patch("src.cache.ModelCache.get_all_models", return_value=models or []),
        patch("src.hf_client.HfApi", return_value=api_mock),
    ]
    return at, patches, api_mock


def test_upload_view_accessible_when_connected():
    at, patches, _ = _make_connected_app()
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
    assert not at.exception
    sidebar_options = [str(r) for r in at.sidebar.radio]
    assert any("Upload" in o for o in sidebar_options)


def test_upload_view_local_file_option_exists():
    at, patches, _ = _make_connected_app()
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
        at.sidebar.radio[0].set_value("Upload Model")
        at.run()
    assert not at.exception
    radio_labels = [str(r) for r in at.radio]
    assert any("Local" in r for r in radio_labels)


def test_upload_view_public_repo_option_exists():
    at, patches, _ = _make_connected_app()
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
        at.sidebar.radio[0].set_value("Upload Model")
        at.run()
    assert not at.exception
    radio_labels = [str(r) for r in at.radio]
    assert any("Public" in r for r in radio_labels)
