"""Inference proxy with a hard 120s read timeout (SC-008).

Routes to the correct upstream API based on hardware type:
- CPU  → HuggingFace TGI at ``/generate``  (``{"inputs": prompt}``)
- GPU  → vLLM OpenAI-compat at ``/v1/chat/completions``

Both paths present an OpenAI-style ``choices[0].message.content`` response to
the caller so the UI/API contract stays uniform.
"""
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


async def forward(
    *,
    endpoint_url: str,
    body: dict,
    hardware_type: str = "cpu",
    model_id: str | None = None,
) -> dict:
    """Forward an OpenAI-style chat payload to the deployed inference endpoint.

    Args:
        endpoint_url: Base URL of the running deployment.
        body: OpenAI-style request body (``messages``, optional ``max_tokens`` /
            ``temperature``).
        hardware_type: ``"cpu"`` routes to TGI ``/generate``; ``"gpu"`` routes
            to vLLM ``/v1/chat/completions``.
        model_id: HuggingFace model ID passed as the ``model`` field for vLLM
            (ignored for CPU/TGI).

    Raises:
        httpx.ReadTimeout: upstream did not respond within 120 s (SC-008).
        InferenceProxyError: any other non-2xx upstream response.
    """
    if hardware_type == "gpu":
        return await _forward_vllm(
            endpoint_url=endpoint_url, body=body, model_id=model_id or "default"
        )
    return await _forward_tgi(endpoint_url=endpoint_url, body=body)


# ---------------------------------------------------------------------------
# CPU path — HuggingFace TGI
# ---------------------------------------------------------------------------

async def _forward_tgi(*, endpoint_url: str, body: dict) -> dict:
    url = endpoint_url.rstrip("/") + "/generate"
    prompt = _messages_to_prompt(body.get("messages", []))
    parameters: dict = {}
    if "max_tokens" in body:
        parameters["max_new_tokens"] = body["max_tokens"]
    if "temperature" in body:
        parameters["temperature"] = body["temperature"]
    if parameters.get("temperature", 1.0) == 0:
        parameters["do_sample"] = False

    tgi_payload: dict = {"inputs": prompt}
    if parameters:
        tgi_payload["parameters"] = parameters

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(url, json=tgi_payload)

    if response.status_code >= 400:
        raise InferenceProxyError(
            code="upstream_error",
            message=f"Upstream returned {response.status_code}: {response.text[:500]}",
            status_code=response.status_code,
        )

    data = response.json()
    text = data.get("generated_text")
    if not isinstance(text, str):
        raise InferenceProxyError(
            code="upstream_invalid_response",
            message="Upstream response did not include 'generated_text'.",
            status_code=502,
        )
    return _to_openai_chat_response(text)


# ---------------------------------------------------------------------------
# GPU path — vLLM OpenAI-compatible server
# ---------------------------------------------------------------------------

async def _forward_vllm(*, endpoint_url: str, body: dict, model_id: str) -> dict:
    url = endpoint_url.rstrip("/") + "/v1/chat/completions"

    messages = body.get("messages", [])
    if not messages:
        raise InferenceProxyError(
            code="invalid_request",
            message="Request must include at least one message.",
            status_code=400,
        )

    vllm_payload: dict = {
        "model": model_id,
        "messages": messages,
    }
    if "max_tokens" in body:
        vllm_payload["max_tokens"] = body["max_tokens"]
    if "temperature" in body:
        vllm_payload["temperature"] = body["temperature"]
    if "stream" in body:
        vllm_payload["stream"] = body["stream"]

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(url, json=vllm_payload)

    if response.status_code >= 400:
        raise InferenceProxyError(
            code="upstream_error",
            message=f"Upstream returned {response.status_code}: {response.text[:500]}",
            status_code=response.status_code,
        )

    # vLLM already returns an OpenAI-format response — pass it straight through.
    return response.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _messages_to_prompt(messages: list[dict]) -> str:
    if not messages:
        raise InferenceProxyError(
            code="invalid_request",
            message="Request must include at least one message.",
            status_code=400,
        )
    parts: list[str] = []
    for msg in messages:
        role = str(msg.get("role", "user")).strip() or "user"
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        parts.append(f"{role}: {content}")
    if not parts:
        raise InferenceProxyError(
            code="invalid_request",
            message="All messages were empty.",
            status_code=400,
        )
    parts.append("assistant:")
    return "\n".join(parts)


def _to_openai_chat_response(text: str) -> dict:
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


__all__ = ["forward", "InferenceProxyError", "INFERENCE_READ_TIMEOUT_SECONDS"]
