"""Lightning AI provider — protocol definition + real SDK implementation.

The protocol is injected via FastAPI dependency injection, enabling
FakeLightningAIProvider to be swapped in for contract tests without
any real Lightning AI calls.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class LightningAIAuthError(Exception):
    """Raised when the Lightning AI SDK rejects an API key (401 / UNAUTHORIZED)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LightningAIServiceError(Exception):
    """Raised on transient Lightning AI platform errors (5xx, timeout, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LightningAINotFoundError(Exception):
    """Raised when a deployment ID is not found on Lightning AI (treat as deleted)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@runtime_checkable
class LightningAIProvider(Protocol):
    async def validate_api_key(self, *, api_key: str) -> None:
        """Raise LightningAIAuthError if the key is invalid or expired."""
        ...

    async def deploy(self, *, hf_model_id: str, api_key: str) -> tuple[str, str | None]:
        """Submit a LitServe+vLLM deployment.

        Returns (lightning_ai_deployment_id, endpoint_url_or_None).
        The endpoint URL is None while the server is still starting.
        """
        ...

    async def get_status(self, *, deployment_id: str, api_key: str) -> tuple[str, str]:
        """Poll deployment status.

        Returns (platform_status, message) where platform_status is one of:
        "deploying", "running", "failed".
        Raises LightningAIAuthError on invalid key, LightningAINotFoundError if gone.
        """
        ...

    async def delete(self, *, deployment_id: str, api_key: str) -> None:
        """Stop and delete a Lightning AI deployment.

        Raises LightningAINotFoundError if already gone (caller should treat as success).
        """
        ...


class RealLightningAIProvider:
    """Calls the real Lightning AI Python SDK."""

    async def validate_api_key(self, *, api_key: str) -> None:
        import asyncio

        await asyncio.to_thread(self._sync_validate, api_key)

    def _sync_validate(self, api_key: str) -> None:
        try:
            from lightning_sdk import LightningClient  # type: ignore[import]

            client = LightningClient(api_key=api_key)
            client.list_apps()
        except Exception as exc:
            msg = str(exc)
            if any(kw in msg.lower() for kw in ("unauthorized", "invalid", "forbidden", "401")):
                raise LightningAIAuthError(f"Lightning AI API key rejected: {msg}") from exc
            raise LightningAIServiceError(f"Lightning AI SDK error during key validation: {msg}") from exc

    async def deploy(self, *, hf_model_id: str, api_key: str) -> tuple[str, str | None]:
        import asyncio

        return await asyncio.to_thread(self._sync_deploy, hf_model_id, api_key)

    def _sync_deploy(self, hf_model_id: str, api_key: str) -> tuple[str, str | None]:
        import tempfile

        from ..services.litserve_gpu import generate

        script_content = generate(hf_model_id)
        slug = hf_model_id.replace("/", "-").replace("_", "-").lower()[:24]
        app_name = f"llmops-{slug}"

        try:
            from lightning_sdk import LightningClient, Machine  # type: ignore[import]

            client = LightningClient(api_key=api_key)
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
                tmp.write(script_content)
                tmp_path = tmp.name

            app = client.run_server(
                script=tmp_path,
                name=app_name,
                machine=Machine.T4,
            )
            return app.id, getattr(app, "url", None)
        except Exception as exc:
            msg = str(exc)
            if any(kw in msg.lower() for kw in ("unauthorized", "invalid", "forbidden", "401")):
                raise LightningAIAuthError(msg) from exc
            raise LightningAIServiceError(f"Lightning AI deploy failed: {msg}") from exc

    async def get_status(self, *, deployment_id: str, api_key: str) -> tuple[str, str]:
        import asyncio

        return await asyncio.to_thread(self._sync_get_status, deployment_id, api_key)

    def _sync_get_status(self, deployment_id: str, api_key: str) -> tuple[str, str]:
        _STATUS_MAP = {
            "starting": ("deploying", "GPU node is starting on Lightning AI…"),
            "running": ("running", "GPU inference server live on Lightning AI."),
            "failed": ("failed", "Lightning AI reported a deployment failure."),
            "stopped": ("deleted", "Lightning AI deployment stopped."),
        }
        try:
            from lightning_sdk import LightningClient  # type: ignore[import]

            client = LightningClient(api_key=api_key)
            app = client.get_app(app_id=deployment_id)
            raw_status = getattr(app, "status", "starting")
            platform_status, message = _STATUS_MAP.get(raw_status, ("deploying", f"Lightning AI status: {raw_status}"))
            if raw_status == "running":
                url = getattr(app, "url", None)
                if url:
                    message = f"GPU inference server live at {url}."
            return platform_status, message
        except Exception as exc:
            msg = str(exc)
            if "not found" in msg.lower() or "404" in msg:
                raise LightningAINotFoundError(deployment_id) from exc
            if any(kw in msg.lower() for kw in ("unauthorized", "invalid", "forbidden", "401")):
                raise LightningAIAuthError(msg) from exc
            raise LightningAIServiceError(f"Lightning AI status poll failed: {msg}") from exc

    async def delete(self, *, deployment_id: str, api_key: str) -> None:
        import asyncio

        await asyncio.to_thread(self._sync_delete, deployment_id, api_key)

    def _sync_delete(self, deployment_id: str, api_key: str) -> None:
        try:
            from lightning_sdk import LightningClient  # type: ignore[import]

            client = LightningClient(api_key=api_key)
            client.delete_app(app_id=deployment_id)
        except Exception as exc:
            msg = str(exc)
            if "not found" in msg.lower() or "404" in msg:
                raise LightningAINotFoundError(deployment_id) from exc
            if any(kw in msg.lower() for kw in ("unauthorized", "invalid", "forbidden", "401")):
                raise LightningAIAuthError(msg) from exc
            raise LightningAIServiceError(f"Lightning AI delete failed: {msg}") from exc


_real_provider = RealLightningAIProvider()


def get_real_provider() -> RealLightningAIProvider:
    return _real_provider


__all__ = [
    "LightningAIProvider",
    "RealLightningAIProvider",
    "LightningAIAuthError",
    "LightningAIServiceError",
    "LightningAINotFoundError",
    "get_real_provider",
]
