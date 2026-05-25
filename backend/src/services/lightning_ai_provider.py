"""Lightning AI provider — protocol definition + real SDK implementation.

The protocol is injected via FastAPI dependency injection, enabling
FakeLightningAIProvider to be swapped in for contract tests without
any real Lightning AI calls.

Authentication uses LIGHTNING_USER_ID + LIGHTNING_API_KEY env vars
(the same values shown in the Lightning AI profile page). A threading
lock ensures only one thread mutates these process-global env vars at
a time.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable

# Process-global lock: the lightning_sdk reads LIGHTNING_USER_ID /
# LIGHTNING_API_KEY from os.environ, so we must serialise any code that
# temporarily swaps those values.
_env_lock = threading.Lock()


class LightningAIAuthError(Exception):
    """Raised when the Lightning AI SDK rejects credentials (401/403)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LightningAIServiceError(Exception):
    """Raised on transient Lightning AI platform errors (5xx, timeout, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LightningAINotFoundError(Exception):
    """Raised when a deployment is not found on Lightning AI (treat as deleted)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class LightningSystemMetrics:
    cpu_utilization: float | None = None
    memory_utilization: float | None = None
    gpu_utilization: float | None = None


@runtime_checkable
class LightningAIProvider(Protocol):
    async def validate_api_key(self, *, api_key: str, lightning_user_id: str) -> None:
        """Raise LightningAIAuthError if the credentials are invalid."""
        ...

    async def deploy(
        self, *, hf_model_id: str, api_key: str, lightning_user_id: str, hf_token: str = ""
    ) -> tuple[str, str | None, str | None, str | None]:
        """Submit a vLLM deployment on Lightning AI.

        Returns (deployment_name, endpoint_url_or_None, teamspace_id, deployment_uuid).
        """
        ...

    async def get_system_metrics(
        self,
        *,
        teamspace_id: str,
        deployment_uuid: str,
        api_key: str,
        lightning_user_id: str,
        start: datetime,
        end: datetime,
    ) -> LightningSystemMetrics | None:
        """Fetch recent CPU/GPU hardware metrics from the Lightning control plane."""
        ...

    async def get_status(
        self, *, deployment_id: str, api_key: str, lightning_user_id: str
    ) -> tuple[str, str]:
        """Poll deployment status.

        Returns (platform_status, message) where platform_status is one of:
        "deploying", "running", "failed", "deleted".
        Raises LightningAIAuthError on invalid credentials,
        LightningAINotFoundError if the deployment is gone.
        """
        ...

    async def delete(self, *, deployment_id: str, api_key: str, lightning_user_id: str) -> None:
        """Stop and delete a Lightning AI deployment.

        Raises LightningAINotFoundError if already gone (caller treats as success).
        """
        ...


def _set_lightning_env(lightning_user_id: str, api_key: str) -> dict[str, str | None]:
    """Swap LIGHTNING_* env vars, returning the previous values for restore."""
    saved = {
        "LIGHTNING_USER_ID": os.environ.get("LIGHTNING_USER_ID"),
        "LIGHTNING_API_KEY": os.environ.get("LIGHTNING_API_KEY"),
    }
    os.environ["LIGHTNING_USER_ID"] = lightning_user_id
    os.environ["LIGHTNING_API_KEY"] = api_key
    return saved


def _restore_lightning_env(saved: dict[str, str | None]) -> None:
    for key, val in saved.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


def _get_teamspace_name(user_api: object, lightning_user_id: str) -> str:  # noqa: ANN001
    """Return the name of the first teamspace the user belongs to.

    Lightning AI personal teamspace names are NOT necessarily the username —
    they are typically 'default-teamspace' or a custom name chosen on signup.
    We fetch the membership list (V1Membership objects) and return the first
    entry's name, falling back to 'default-teamspace' if the list is empty.
    """
    memberships = user_api._get_all_teamspace_memberships(lightning_user_id)  # noqa: SLF001
    if not memberships:
        return "default-teamspace"
    # Prefer the entry marked is_default; fall back to the first entry.
    for m in memberships:
        if getattr(m, "is_default", False):
            return m.name
    return memberships[0].name


def _is_auth_error(msg: str) -> bool:
    """True only for genuine authentication failures (wrong/expired key, 401).

    A 403 Forbidden / PERMISSION_DENIED (gRPC code 7) means the key is valid
    but the account lacks permission (e.g. no GPU plan).  We intentionally do
    NOT classify 403 as an auth error so we don't incorrectly mark a valid key
    as invalid.
    """
    lower = msg.lower()
    # "response: 401" or bare "401" in SDK error messages
    if "401" in msg:
        return True
    # SDK sometimes surfaces these words for true authentication failures
    if any(kw in lower for kw in ("unauthenticated", "invalid api key", "token expired")):
        return True
    return False


def _is_permission_error(msg: str) -> bool:
    """True for 403/PERMISSION_DENIED — valid key but insufficient account privileges."""
    return "403" in msg or "forbidden" in msg.lower() or "permission_denied" in msg.lower()


class RealLightningAIProvider:
    """Calls the real Lightning AI Python SDK.

    All SDK objects are instantiated inside the lock so they pick up the
    correct LIGHTNING_USER_ID / LIGHTNING_API_KEY values.
    """

    async def validate_api_key(self, *, api_key: str, lightning_user_id: str) -> None:
        import asyncio

        await asyncio.to_thread(self._sync_validate, api_key, lightning_user_id)

    def _sync_validate(self, api_key: str, lightning_user_id: str) -> None:
        with _env_lock:
            saved = _set_lightning_env(lightning_user_id, api_key)
            try:
                from lightning_sdk.api import UserApi  # type: ignore[import]

                UserApi()._get_user_by_id(lightning_user_id)  # noqa: SLF001
            except ValueError as exc:
                # _get_user_by_id raises ValueError when the user_id is not found.
                raise LightningAIAuthError(
                    f"Lightning AI User ID not found: {exc}. "
                    "Check that LIGHTNING_USER_ID matches your profile UUID."
                ) from exc
            except Exception as exc:
                msg = str(exc)
                if _is_auth_error(msg):
                    raise LightningAIAuthError(f"Lightning AI credentials rejected: {msg}") from exc
                raise LightningAIServiceError(f"Lightning AI validation failed: {msg}") from exc
            finally:
                _restore_lightning_env(saved)

    async def deploy(
        self, *, hf_model_id: str, api_key: str, lightning_user_id: str, hf_token: str = ""
    ) -> tuple[str, str | None, str | None, str | None]:
        import asyncio

        return await asyncio.to_thread(
            self._sync_deploy, hf_model_id, api_key, lightning_user_id, hf_token
        )

    def _sync_deploy(
        self, hf_model_id: str, api_key: str, lightning_user_id: str, hf_token: str = ""
    ) -> tuple[str, str | None, str | None, str | None]:
        with _env_lock:
            saved = _set_lightning_env(lightning_user_id, api_key)
            try:
                from lightning_sdk import Deployment, Machine  # type: ignore[import]
                from lightning_sdk.api import UserApi  # type: ignore[import]

                user_api = UserApi()
                user_record = user_api._get_user_by_id(lightning_user_id)  # noqa: SLF001
                username = user_record.username
                teamspace_name = _get_teamspace_name(user_api, lightning_user_id)

                slug = hf_model_id.replace("/", "-").replace("_", "-").lower()[:24].strip("-")
                app_name = f"llmops-{slug}"

                dep = Deployment(name=app_name, teamspace=teamspace_name, user=username)
                env: dict[str, str] = {}
                if hf_token:
                    env["HF_TOKEN"] = hf_token
                dep.start(
                    machine=Machine.T4,
                    image="vllm/vllm-openai:latest",
                    command=f"--model {hf_model_id} --host 0.0.0.0 --port 8000",
                    ports=[8000],
                    **({"env": env} if env else {}),
                )

                urls = dep.urls
                endpoint_url = urls[0] if urls else None
                internal = dep._deployment  # noqa: SLF001
                teamspace_id = internal.project_id if internal is not None else dep._teamspace.id  # noqa: SLF001
                deployment_uuid = internal.id if internal is not None else None
                return dep._name, endpoint_url, teamspace_id, deployment_uuid  # noqa: SLF001

            except LightningAIAuthError:
                raise
            except Exception as exc:
                msg = str(exc)
                if _is_auth_error(msg):
                    raise LightningAIAuthError(msg) from exc
                if _is_permission_error(msg):
                    raise LightningAIServiceError(
                        "Lightning AI returned 403 Forbidden when creating the deployment. "
                        "This typically means your account plan does not include GPU deployments "
                        "(T4 is a paid tier). Please check your Lightning AI plan and billing at "
                        "https://lightning.ai/settings."
                    ) from exc
                raise LightningAIServiceError(f"Lightning AI deploy failed: {msg}") from exc
            finally:
                _restore_lightning_env(saved)

    async def get_system_metrics(
        self,
        *,
        teamspace_id: str,
        deployment_uuid: str,
        api_key: str,
        lightning_user_id: str,
        start: datetime,
        end: datetime,
    ) -> LightningSystemMetrics | None:
        import asyncio

        return await asyncio.to_thread(
            self._sync_get_system_metrics,
            teamspace_id,
            deployment_uuid,
            api_key,
            lightning_user_id,
            start,
            end,
        )

    def _sync_get_system_metrics(
        self,
        teamspace_id: str,
        deployment_uuid: str,
        api_key: str,
        lightning_user_id: str,
        start: datetime,
        end: datetime,
    ) -> LightningSystemMetrics | None:
        with _env_lock:
            saved = _set_lightning_env(lightning_user_id, api_key)
            try:
                from lightning_sdk.lightning_cloud.rest_client import (
                    LightningClient,  # type: ignore[import]
                )

                client = LightningClient(retry=False)
                job_ids = _list_lightning_job_ids(
                    client,
                    teamspace_id=teamspace_id,
                    deployment_uuid=deployment_uuid,
                )
                query_kwargs: dict = {
                    "project_id": teamspace_id,
                    "deployment_id": deployment_uuid,
                    "start": start,
                    "end": end,
                }
                if job_ids:
                    query_kwargs["ids"] = job_ids

                response = client.jobs_service_get_job_system_metrics(**query_kwargs)
                metrics = _parse_lightning_system_metrics(response)
                if metrics is not None:
                    return metrics

                # Widen the window — Lightning may lag a few minutes behind live state.
                if (end - start).total_seconds() < 3600:
                    wider = dict(query_kwargs)
                    wider["start"] = end - timedelta(hours=1)
                    response = client.jobs_service_get_job_system_metrics(**wider)
                    return _parse_lightning_system_metrics(response)
                return None
            except Exception as exc:
                msg = str(exc)
                if _is_auth_error(msg):
                    raise LightningAIAuthError(msg) from exc
                raise LightningAIServiceError(
                    f"Lightning AI system metrics fetch failed: {msg}"
                ) from exc
            finally:
                _restore_lightning_env(saved)

    async def get_status(
        self, *, deployment_id: str, api_key: str, lightning_user_id: str
    ) -> tuple[str, str]:
        import asyncio

        return await asyncio.to_thread(
            self._sync_get_status, deployment_id, api_key, lightning_user_id
        )

    def _sync_get_status(
        self, deployment_id: str, api_key: str, lightning_user_id: str
    ) -> tuple[str, str]:
        with _env_lock:
            saved = _set_lightning_env(lightning_user_id, api_key)
            try:
                from lightning_sdk import Deployment  # type: ignore[import]
                from lightning_sdk.api import UserApi  # type: ignore[import]

                user_api = UserApi()
                username = user_api._get_user_by_id(lightning_user_id).username  # noqa: SLF001
                teamspace_name = _get_teamspace_name(user_api, lightning_user_id)
                dep = Deployment(name=deployment_id, teamspace=teamspace_name, user=username)

                if not dep.is_started:
                    raise LightningAINotFoundError(deployment_id)

                failing = dep.failing_replicas or 0
                if failing > 0:
                    return "failed", "Lightning AI reported failing replicas."

                if dep.is_stopped:
                    return "deleted", "Lightning AI deployment stopped."

                running = dep.running_replicas or 0
                urls = dep.urls or []
                if running > 0 and urls:
                    url = urls[0]
                    return "running", f"GPU inference server live at {url}."

                return "deploying", "Waiting for GPU node to come online on Lightning AI…"

            except LightningAINotFoundError:
                raise
            except Exception as exc:
                msg = str(exc)
                if "not found" in msg.lower() or "404" in msg:
                    raise LightningAINotFoundError(deployment_id) from exc
                if _is_auth_error(msg):
                    raise LightningAIAuthError(msg) from exc
                raise LightningAIServiceError(f"Lightning AI status poll failed: {msg}") from exc
            finally:
                _restore_lightning_env(saved)

    async def delete(self, *, deployment_id: str, api_key: str, lightning_user_id: str) -> None:
        import asyncio

        await asyncio.to_thread(self._sync_delete, deployment_id, api_key, lightning_user_id)

    def _sync_delete(self, deployment_id: str, api_key: str, lightning_user_id: str) -> None:
        with _env_lock:
            saved = _set_lightning_env(lightning_user_id, api_key)
            try:
                from lightning_sdk import Deployment  # type: ignore[import]
                from lightning_sdk.api import UserApi  # type: ignore[import]

                user_api = UserApi()
                username = user_api._get_user_by_id(lightning_user_id).username  # noqa: SLF001
                teamspace_name = _get_teamspace_name(user_api, lightning_user_id)
                dep = Deployment(name=deployment_id, teamspace=teamspace_name, user=username)

                if not dep.is_started:
                    raise LightningAINotFoundError(deployment_id)

                # dep.stop() only scales to zero replicas — the deployment still
                # appears on the dashboard.  We call the underlying
                # jobs_service_delete_deployment to fully remove it.
                internal_dep = dep._deployment  # noqa: SLF001
                dep._deployment_api._client.jobs_service_delete_deployment(  # noqa: SLF001
                    project_id=internal_dep.project_id,
                    id=internal_dep.id,
                )

            except LightningAINotFoundError:
                raise
            except Exception as exc:
                msg = str(exc)
                if "not found" in msg.lower() or "404" in msg:
                    raise LightningAINotFoundError(deployment_id) from exc
                if _is_auth_error(msg):
                    raise LightningAIAuthError(msg) from exc
                raise LightningAIServiceError(f"Lightning AI delete failed: {msg}") from exc
            finally:
                _restore_lightning_env(saved)


def _list_lightning_job_ids(
    client: object,
    *,
    teamspace_id: str,
    deployment_uuid: str,
) -> list[str]:
    """Return running replica job IDs for a deployment."""
    try:
        response = client.jobs_service_list_jobs(  # type: ignore[attr-defined]
            project_id=teamspace_id,
            deployment_id=deployment_uuid,
            state="running",
            limit=10,
        )
    except Exception:
        return []
    jobs = getattr(response, "jobs", None) or []
    return [job.id for job in jobs if getattr(job, "id", None)]


def _parse_lightning_system_metrics(response: object) -> LightningSystemMetrics | None:
    system_metrics = getattr(response, "system_metrics", None) or {}
    if not system_metrics:
        return None
    latest = None
    for metrics_list in system_metrics.values():
        entries = getattr(metrics_list, "metrics", None) or []
        for entry in entries:
            if latest is None:
                latest = entry
                continue
            entry_ts = getattr(entry, "timestamp", None)
            latest_ts = getattr(latest, "timestamp", None)
            if entry_ts is not None and latest_ts is not None and entry_ts > latest_ts:
                latest = entry
    if latest is None:
        return None

    cpu_util: float | None = None
    memory_util: float | None = None
    gpu_util: float | None = None

    cpu = getattr(latest, "cpu", None)
    if cpu is not None:
        pct = getattr(cpu, "percentage", None)
        if pct is not None:
            cpu_util = float(pct) / 100.0

    gpus = getattr(latest, "gpu", None) or []
    if gpus:
        first_gpu = gpus[0]
        util = getattr(first_gpu, "utilisation", None)
        if util is not None:
            gpu_util = float(util) / 100.0
        memory_util = _gpu_memory_utilization(first_gpu)

    if cpu_util is None and memory_util is None and gpu_util is None:
        return None
    return LightningSystemMetrics(
        cpu_utilization=cpu_util,
        memory_utilization=memory_util,
        gpu_utilization=gpu_util,
    )


def _gpu_memory_utilization(gpu: object) -> float | None:
    """Return GPU VRAM used/total as a 0-1 ratio."""
    mem_total = getattr(gpu, "memory_total", None)
    mem_used = getattr(gpu, "memory_used", None)
    if mem_total is not None and int(mem_total) > 0 and mem_used is not None:
        return min(float(mem_used) / float(mem_total), 1.0)
    mem_pct = getattr(gpu, "utilisation_memory", None)
    if mem_pct is not None:
        return min(float(mem_pct) / 100.0, 1.0)
    return None


_real_provider = RealLightningAIProvider()


def get_real_provider() -> RealLightningAIProvider:
    return _real_provider


__all__ = [
    "LightningAIProvider",
    "RealLightningAIProvider",
    "LightningAIAuthError",
    "LightningAIServiceError",
    "LightningAINotFoundError",
    "LightningSystemMetrics",
    "get_real_provider",
]
