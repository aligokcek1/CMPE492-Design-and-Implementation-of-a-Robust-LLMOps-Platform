import io
from unittest.mock import MagicMock, patch

import pytest

from src.hf_client import HFClient, MAX_FILE_SIZE_BYTES, REPO_NAME_PREFIX


@pytest.fixture
def mock_api():
    with patch("src.hf_client.HfApi") as MockHfApi:
        api_instance = MagicMock()
        MockHfApi.return_value = api_instance
        yield api_instance


# --- US1: is_valid_token, get_username ---


def test_is_valid_token_returns_true(mock_api):
    mock_api.whoami.return_value = {"name": "testuser"}
    client = HFClient("valid_token")
    assert client.is_valid_token() is True


def test_is_valid_token_returns_false_on_exception(mock_api):
    mock_api.whoami.side_effect = Exception("Unauthorized")
    client = HFClient("invalid_token")
    assert client.is_valid_token() is False


def test_get_username(mock_api):
    mock_api.whoami.return_value = {"name": "testuser"}
    client = HFClient("valid_token")
    assert client.get_username() == "testuser"


# --- US2: verify_public_repo, upload_local_file ---


def test_verify_public_repo_accessible(mock_api):
    mock_api.repo_info.return_value = MagicMock()
    client = HFClient("token")
    assert client.verify_public_repo("public-user/some-model") is True


def test_verify_public_repo_not_accessible(mock_api):
    mock_api.repo_info.side_effect = Exception("Repository not found")
    client = HFClient("token")
    assert client.verify_public_repo("non-existent/repo") is False


def test_upload_local_file_success(mock_api):
    mock_api.whoami.return_value = {"name": "testuser"}
    mock_api.create_repo.return_value = MagicMock()
    mock_api.upload_file.return_value = MagicMock()
    client = HFClient("token")
    file_obj = io.BytesIO(b"fake model data")
    result = client.upload_local_file(file_obj, "model.bin", "mymodel")
    assert result == f"testuser/{REPO_NAME_PREFIX}mymodel"
    mock_api.create_repo.assert_called_once()
    mock_api.upload_file.assert_called_once()


def test_upload_local_file_exceeds_size_limit(mock_api):
    client = HFClient("token")
    large_data = b"x" * (MAX_FILE_SIZE_BYTES + 1)
    file_obj = io.BytesIO(large_data)
    with pytest.raises(ValueError, match="500MB"):
        client.upload_local_file(file_obj, "large.bin", "mymodel")


def test_upload_local_file_repo_name_convention(mock_api):
    mock_api.whoami.return_value = {"name": "testuser"}
    mock_api.create_repo.return_value = MagicMock()
    mock_api.upload_file.return_value = MagicMock()
    client = HFClient("token")
    file_obj = io.BytesIO(b"data")
    result = client.upload_local_file(file_obj, "model.bin", "gpt-2")
    assert result.startswith("testuser/inference-app-")
    assert "gpt-2" in result
