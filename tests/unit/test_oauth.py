from unittest.mock import MagicMock, patch

import pytest

from src.oauth import HFOAuthService


@pytest.fixture
def service():
    return HFOAuthService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8501/",
    )


# ---------------------------------------------------------------------------
# get_authorization_url  (FR-002)
# ---------------------------------------------------------------------------


def test_get_authorization_url_returns_tuple(service):
    result = service.get_authorization_url()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_get_authorization_url_url_points_to_huggingface(service):
    url, _ = service.get_authorization_url()
    assert "huggingface.co" in url


def test_get_authorization_url_state_is_nonempty_string(service):
    _, state = service.get_authorization_url()
    assert isinstance(state, str)
    assert len(state) > 0


def test_get_authorization_url_produces_unique_states(service):
    _, state1 = service.get_authorization_url()
    _, state2 = service.get_authorization_url()
    assert state1 != state2


# ---------------------------------------------------------------------------
# fetch_token — state validation (FR-003, FR-004, FR-005)
# ---------------------------------------------------------------------------


def test_fetch_token_raises_on_state_mismatch(service):
    with pytest.raises(ValueError, match="[Ss]tate"):
        service.fetch_token(
            authorization_response_url="http://localhost:8501/?code=abc&state=WRONG",
            saved_state="CORRECT",
        )


def test_fetch_token_calls_token_endpoint_on_valid_state(service):
    mock_token = {"access_token": "hf_abc123", "token_type": "Bearer"}
    with patch("src.oauth.OAuth2Session") as MockSession:
        mock_session = MagicMock()
        mock_session.fetch_token.return_value = mock_token
        MockSession.return_value = mock_session

        result = service.fetch_token(
            authorization_response_url="http://localhost:8501/?code=abc&state=MATCH",
            saved_state="MATCH",
        )

    assert result["access_token"] == "hf_abc123"


def test_fetch_token_passes_client_secret_to_endpoint(service):
    mock_token = {"access_token": "hf_xyz", "token_type": "Bearer"}
    with patch("src.oauth.OAuth2Session") as MockSession:
        mock_session = MagicMock()
        mock_session.fetch_token.return_value = mock_token
        MockSession.return_value = mock_session

        service.fetch_token(
            authorization_response_url="http://localhost:8501/?code=abc&state=MATCH",
            saved_state="MATCH",
        )

        call_kwargs = mock_session.fetch_token.call_args
        assert call_kwargs is not None
        # client_secret must be forwarded so the token endpoint can authenticate the app
        assert "test_client_secret" in str(call_kwargs)
