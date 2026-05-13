"""Public-HF model gate for feature 007.

Only **text-generation / NLP** models are supported for real GKE deployment in
v1 (per spec Assumption #3). This module parses HF metadata and returns a
boolean + reason so the API layer can return a structured 400 for unsupported
types (image classification, ASR, etc).
"""
from __future__ import annotations

import asyncio
from typing import Any

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError

_SUPPORTED_PIPELINE_TAGS = {
    "text-generation",
    "text2text-generation",
    "conversational",
}


async def is_supported_text_generation_model(
    hf_model_id: str,
    *,
    hf_token: str | None = None,
    timeout: int = 10,
) -> tuple[bool, str, str]:
    """Returns ``(is_supported, pipeline_tag, reason)``.

    When *hf_token* is provided, uses it for authentication so that private
    and gated repositories can be validated. The *timeout* (seconds) is
    applied to the HF Hub network call; on timeout the function returns a
    structured ``(False, "unreachable", <message>)`` tuple rather than raising.
    """
    import requests

    loop = asyncio.get_event_loop()
    api = HfApi(token=hf_token or None)

    def _fetch() -> Any:
        try:
            return api.model_info(hf_model_id, token=hf_token or None, timeout=timeout)
        except RepositoryNotFoundError as exc:
            raise RepositoryNotFoundError(
                f"HuggingFace repo '{hf_model_id}' not found."
            ) from exc

    try:
        info = await loop.run_in_executor(None, _fetch)
    except RepositoryNotFoundError as exc:
        return False, "unknown", str(exc)
    except HfHubHTTPError as exc:
        if exc.response is not None and exc.response.status_code == 403:
            return False, "access_denied", (
                f"Token lacks read access to '{hf_model_id}'. "
                "Ensure your HuggingFace token has read permission for this repository."
            )
        return False, "unknown", f"Failed to fetch HF metadata: {exc}"
    except (requests.exceptions.Timeout, TimeoutError, OSError):
        return False, "unreachable", "HuggingFace Hub is currently unreachable, please retry."
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "timeout" in msg or "timed out" in msg or "connection" in msg:
            return False, "unreachable", "HuggingFace Hub is currently unreachable, please retry."
        return False, "unknown", f"Failed to fetch HF metadata: {exc}"

    pipeline_tag = getattr(info, "pipeline_tag", None) or "unknown"
    if pipeline_tag in _SUPPORTED_PIPELINE_TAGS:
        return True, pipeline_tag, "ok"

    return (
        False,
        pipeline_tag,
        f"Model pipeline tag is '{pipeline_tag}'; only text-generation / "
        "NLP models are supported for real deployment in this version.",
    )


async def get_display_name(hf_model_id: str) -> str:
    """Best-effort human-friendly label for the list view."""
    loop = asyncio.get_event_loop()
    api = HfApi()

    def _fetch() -> str:
        try:
            info = api.model_info(hf_model_id, token=None)
            return info.modelId or hf_model_id
        except Exception:  # noqa: BLE001 — display-only, never propagate
            return hf_model_id

    return await loop.run_in_executor(None, _fetch)


__all__ = ["is_supported_text_generation_model", "get_display_name"]
