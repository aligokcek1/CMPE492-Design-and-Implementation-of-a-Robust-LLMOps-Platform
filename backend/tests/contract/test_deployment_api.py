import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from src.main import app
from src.models.deployment import MockDeploymentResponse


@pytest.fixture
def transport():
    return ASGITransport(app=app)


async def _session_auth_headers(client: AsyncClient) -> dict[str, str]:
    with patch("src.api.auth.verify_hf_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = "test_user"
        login = await client.post("/api/auth/verify", json={"token": "hf_valid_token"})
    token = login.json()["session_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_mock_deploy_cpu_success(transport):
    mock_response = MockDeploymentResponse(
        status="mock_success",
        message="Mock deployment of 'user/model' on CPU completed successfully.",
    )
    with patch("src.api.deployment.mock_deploy", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await _session_auth_headers(client)
            response = await client.post(
                "/api/deployment/mock",
                json={"model_repository": "user/model", "resource_type": "CPU"},
                headers=headers,
            )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "mock_success"
    assert "message" in data


@pytest.mark.asyncio
async def test_mock_deploy_gpu_success(transport):
    mock_response = MockDeploymentResponse(
        status="mock_success",
        message="Mock deployment of 'user/model' on GPU completed successfully.",
    )
    with patch("src.api.deployment.mock_deploy", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await _session_auth_headers(client)
            response = await client.post(
                "/api/deployment/mock",
                json={"model_repository": "user/model", "resource_type": "GPU"},
                headers=headers,
            )
    assert response.status_code == 200
    assert response.json()["status"] == "mock_success"


@pytest.mark.asyncio
async def test_mock_deploy_missing_token(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/deployment/mock",
            json={"model_repository": "user/model", "resource_type": "CPU"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mock_deploy_invalid_resource_type(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        response = await client.post(
            "/api/deployment/mock",
            json={"model_repository": "user/model", "resource_type": "TPU"},
            headers=headers,
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_mock_deploy_idempotency_replay(transport):
    mock_response = MockDeploymentResponse(
        status="mock_success",
        message="Mock deployment of 'user/model' on CPU completed successfully.",
    )
    with patch("src.api.deployment.mock_deploy", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await _session_auth_headers(client)
            headers["X-Idempotency-Key"] = "retry-deploy-1"
            first = await client.post(
                "/api/deployment/mock",
                json={"model_repository": "user/model", "resource_type": "CPU"},
                headers=headers,
            )
            second = await client.post(
                "/api/deployment/mock",
                json={"model_repository": "user/model", "resource_type": "CPU"},
                headers=headers,
            )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert mock_fn.call_count == 1
