from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

_MODELS_NOT_DEPLOYED = [
    {
        "id": 1,
        "name": "TestModel",
        "source_type": "LOCAL_PC",
        "hf_repo_id": "testuser/inference-app-testmodel",
        "is_deployed": 0,
        "deployed_at": None,
        "last_synced": "2026-03-14T00:00:00",
    }
]

_MODELS_DEPLOYED = [
    {
        "id": 1,
        "name": "TestModel",
        "source_type": "LOCAL_PC",
        "hf_repo_id": "testuser/inference-app-testmodel",
        "is_deployed": 1,
        "deployed_at": "2026-03-14T10:00:00",
        "last_synced": "2026-03-14T00:00:00",
    }
]


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
    return at, patches


def test_deploy_view_shows_no_models_message():
    at, patches = _make_connected_app(models=[])
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
        at.sidebar.radio[0].set_value("Deploy & Inference")
        at.run()
    assert not at.exception


def test_deploy_view_renders_undeployed_model():
    at, patches = _make_connected_app(models=_MODELS_NOT_DEPLOYED)
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
        at.sidebar.radio[0].set_value("Deploy & Inference")
        at.run()
    assert not at.exception


def test_deploy_view_renders_deployed_model_with_inference():
    at, patches = _make_connected_app(models=_MODELS_DEPLOYED)
    with patches[0], patches[1], patches[2], patches[3]:
        at.run()
        at.sidebar.radio[0].set_value("Deploy & Inference")
        at.run()
    assert not at.exception
