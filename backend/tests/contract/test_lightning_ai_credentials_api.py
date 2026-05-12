"""Contract tests for GET/POST/DELETE /api/lightning/credentials (T015)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _session_auth_headers(client: AsyncClient) -> dict[str, str]:
    with patch("src.api.auth.verify_hf_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = "test_user"
        login = await client.post("/api/auth/verify", json={"token": "hf_valid_token"})
    token = login.json()["session_token"]
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# GET /api/lightning/credentials                                               #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_get_credentials_not_configured(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        resp = await client.get("/api/lightning/credentials", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    assert body["validation_status"] is None


@pytest.mark.asyncio
async def test_get_credentials_requires_session_401(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/lightning/credentials")
    assert resp.status_code == 401


# --------------------------------------------------------------------------- #
# POST /api/lightning/credentials                                              #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_save_valid_key_returns_configured_and_valid(transport, fake_lightning_ai_provider):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        resp = await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-validkey123"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["configured"] is True
    assert body["validation_status"] == "valid"
    assert "api_key" not in body  # key must never be returned


@pytest.mark.asyncio
async def test_save_invalid_key_returns_400(transport, fake_lightning_ai_provider):
    fake_lightning_ai_provider.reject_key = True

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        resp = await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-badkey"},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "lightning_auth_error"


@pytest.mark.asyncio
async def test_save_credentials_requires_session_401(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/lightning/credentials",
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-validkey"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_replace_existing_key(transport, fake_lightning_ai_provider):
    """Saving a second key replaces the first."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-firstkey"},
        )
        resp2 = await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-secondkey"},
        )
        status_resp = await client.get("/api/lightning/credentials", headers=headers)

    assert resp2.status_code == 200
    body = status_resp.json()
    assert body["configured"] is True
    assert body["validation_status"] == "valid"


# --------------------------------------------------------------------------- #
# DELETE /api/lightning/credentials                                            #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_delete_credentials_returns_204(transport, fake_lightning_ai_provider):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-validkey"},
        )
        resp = await client.delete("/api/lightning/credentials", headers=headers)

    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_then_get_shows_not_configured(transport, fake_lightning_ai_provider):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-validkey"},
        )
        await client.delete("/api/lightning/credentials", headers=headers)
        resp = await client.get("/api/lightning/credentials", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["configured"] is False


@pytest.mark.asyncio
async def test_delete_idempotent_when_not_configured(transport):
    """DELETE when no key configured is a no-op (204)."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        resp = await client.delete("/api/lightning/credentials", headers=headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_save_after_delete_works(transport, fake_lightning_ai_provider):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _session_auth_headers(client)
        await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-first"},
        )
        await client.delete("/api/lightning/credentials", headers=headers)
        resp = await client.post(
            "/api/lightning/credentials",
            headers=headers,
            json={"lightning_user_id": "fake-lai-uid-123", "api_key": "lai-second"},
        )

    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    assert resp.json()["validation_status"] == "valid"
