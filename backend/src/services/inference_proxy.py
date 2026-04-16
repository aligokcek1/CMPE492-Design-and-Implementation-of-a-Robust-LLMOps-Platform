"""OpenAI-style inference proxy with a hard 120s read timeout (SC-008)."""
from __future__ import annotations

import httpx

INFERENCE_READ_TIMEOUT_SECONDS = 120


_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=INFERENCE_READ_TIMEOUT_SECONDS,
    write=10.0,
    pool=5.0,
)


class InferenceProxyError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def forward(*, endpoint_url: str, body: dict) -> dict:
    """Forward an OpenAI chat-completions request to the vLLM endpoint.

    Raises:
        httpx.ReadTimeout: the upstream didn't respond within 120s (SC-008).
        InferenceProxyError: any other non-2xx upstream response.
    """
    url = endpoint_url.rstrip("/") + "/v1/chat/completions"

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(url, json=body)

    if response.status_code >= 400:
        raise InferenceProxyError(
            code="upstream_error",
            message=f"Upstream returned {response.status_code}: {response.text[:500]}",
            status_code=response.status_code,
        )

    return response.json()


__all__ = ["forward", "InferenceProxyError", "INFERENCE_READ_TIMEOUT_SECONDS"]
