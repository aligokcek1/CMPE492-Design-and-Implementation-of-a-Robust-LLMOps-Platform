"""In-memory fake Lightning AI provider for contract tests.

Never touches the real Lightning AI SDK. Deterministic and configurable.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from .lightning_ai_provider import (
    LightningAIAuthError,
    LightningAINotFoundError,
    LightningSystemMetrics,
)


class FakeLightningAIProvider:
    """Simulates Lightning AI without any network calls.

    Configure before each test by setting instance attributes:
    - ``reject_key``: if True, validate_api_key raises LightningAIAuthError
    - ``deploy_raises``: if set to an exception class, deploy() raises it
    - ``status_sequence``: list of (platform_status, message) tuples returned
      in order by successive get_status() calls (cycles on the last entry)
    """

    def __init__(self) -> None:
        self.reject_key: bool = False
        self.deploy_raises: type[Exception] | None = None
        self._deployments: dict[str, dict] = {}
        self.status_sequence: list[tuple[str, str]] = [
            ("deploying", "Submitting to Lightning AI…"),
            ("running", "GPU inference server live on Lightning AI."),
        ]
        self._status_call_counts: dict[str, int] = {}
        self.deleted_ids: set[str] = set()
        self.system_metrics: LightningSystemMetrics | None = LightningSystemMetrics(
            cpu_utilization=0.12,
            memory_utilization=0.45,
            gpu_utilization=0.68,
        )

    async def validate_api_key(self, *, api_key: str, lightning_user_id: str = "") -> None:
        if self.reject_key:
            raise LightningAIAuthError("Fake: API key rejected.")

    async def deploy(
        self, *, hf_model_id: str, api_key: str, lightning_user_id: str = "", hf_token: str = ""
    ) -> tuple[str, str | None, str | None, str | None]:
        if self.reject_key:
            raise LightningAIAuthError("Fake: API key rejected during deploy.")
        if self.deploy_raises is not None:
            raise self.deploy_raises("Fake deploy error.")
        deployment_id = f"fake-lai-{uuid.uuid4().hex[:8]}"
        endpoint_url = f"http://fake-lightning.ai/{deployment_id}"
        self._deployments[deployment_id] = {
            "hf_model_id": hf_model_id,
            "endpoint_url": endpoint_url,
        }
        return deployment_id, endpoint_url, "fake-teamspace-id", f"uuid-{deployment_id}"

    async def get_system_metrics(
        self,
        *,
        teamspace_id: str,
        deployment_uuid: str,
        api_key: str,
        lightning_user_id: str = "",
        start: datetime,
        end: datetime,
    ) -> LightningSystemMetrics | None:
        return self.system_metrics

    async def get_status(
        self, *, deployment_id: str, api_key: str, lightning_user_id: str = ""
    ) -> tuple[str, str]:
        if deployment_id in self.deleted_ids:
            raise LightningAINotFoundError(deployment_id)
        if self.reject_key:
            raise LightningAIAuthError("Fake: API key invalid during status poll.")
        count = self._status_call_counts.get(deployment_id, 0)
        self._status_call_counts[deployment_id] = count + 1
        idx = min(count, len(self.status_sequence) - 1)
        return self.status_sequence[idx]

    async def delete(
        self, *, deployment_id: str, api_key: str, lightning_user_id: str = ""
    ) -> None:
        if deployment_id not in self._deployments and deployment_id not in self.deleted_ids:
            raise LightningAINotFoundError(deployment_id)
        self._deployments.pop(deployment_id, None)
        self.deleted_ids.add(deployment_id)


__all__ = ["FakeLightningAIProvider"]
