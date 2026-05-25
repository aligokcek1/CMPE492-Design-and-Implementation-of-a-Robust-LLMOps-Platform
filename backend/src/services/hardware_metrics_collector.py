"""Poll platform APIs and export per-deployment hardware gauges to Prometheus."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ..db.models import DeploymentRow
from .deployment_store import deployment_store
from .gcp_fake_provider import FakeGCPProvider
from .gcp_provider import GCPProvider
from .lightning_ai_credentials_store import lightning_ai_credentials_store
from .lightning_ai_provider import LightningAIProvider, LightningAIServiceError
from .metrics_recorder import record_hardware_metrics
from .vllm_manifest import _safe_name

logger = logging.getLogger("llmops.hardware_metrics_collector")

HARDWARE_POLL_INTERVAL_SECONDS = 15
_CPU_LIMIT_CORES = 1.0
# Must match TGI manifest memory limit in vllm_manifest.py (4Gi).
_CPU_MEMORY_LIMIT_BYTES = 4 * 1024 * 1024 * 1024
_DEFAULT_K8S_NAMESPACE = "default"


def _metrics_disabled() -> bool:
    return os.environ.get("LLMOPS_METRICS_DISABLED") == "1"


@dataclass(frozen=True)
class HardwareSnapshot:
    cpu_utilization: float | None = None
    memory_utilization: float | None = None
    gpu_utilization: float | None = None


class HardwareMetricsCollector:
    def __init__(
        self,
        *,
        gcp_provider_factory: Callable[[], GCPProvider] | None = None,
        lightning_ai_provider_factory: Callable[[], LightningAIProvider] | None = None,
    ) -> None:
        self._gcp_provider_factory = gcp_provider_factory
        self._lightning_ai_provider_factory = lightning_ai_provider_factory

    async def poll_running_deployments(self) -> None:
        if _metrics_disabled():
            return
        rows = deployment_store.list_by_status("running")
        for row in rows:
            try:
                snapshot = await self._collect_for_deployment(row)
                if snapshot is None:
                    continue
                record_hardware_metrics(
                    deployment_id=row.id,
                    user_id=row.user_id,
                    hardware_type=row.hardware_type,
                    cpu_utilization=snapshot.cpu_utilization,
                    memory_utilization=snapshot.memory_utilization,
                    gpu_utilization=snapshot.gpu_utilization,
                )
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Hardware metrics collection failed for %s",
                    row.id,
                    exc_info=True,
                )

    async def _collect_for_deployment(self, row: DeploymentRow) -> HardwareSnapshot | None:
        if row.hardware_type == "gpu":
            return await self._collect_lightning(row)
        return await self._collect_gke(row)

    async def _collect_lightning(self, row: DeploymentRow) -> HardwareSnapshot | None:
        if not row.lightning_teamspace_id or not row.lightning_deployment_uuid:
            return None
        creds = await lightning_ai_credentials_store.get_credentials(user_id=row.user_id)
        if creds is None:
            return None
        provider = self._lightning_provider()
        end = datetime.now(UTC)
        start = end - timedelta(minutes=15)
        try:
            metrics = await provider.get_system_metrics(
                teamspace_id=row.lightning_teamspace_id,
                deployment_uuid=row.lightning_deployment_uuid,
                api_key=creds.api_key,
                lightning_user_id=creds.lightning_user_id,
                start=start,
                end=end,
            )
        except LightningAIServiceError as exc:
            logger.warning("Lightning system metrics unavailable for %s: %s", row.id, exc)
            return None
        if metrics is None:
            logger.info(
                "Lightning system metrics empty for deployment %s (teamspace=%s, dep=%s)",
                row.id,
                row.lightning_teamspace_id,
                row.lightning_deployment_uuid,
            )
            return None
        return HardwareSnapshot(
            cpu_utilization=metrics.cpu_utilization,
            memory_utilization=metrics.memory_utilization,
            gpu_utilization=metrics.gpu_utilization,
        )

    async def _collect_gke(self, row: DeploymentRow) -> HardwareSnapshot | None:
        if not row.gcp_project_id or not row.gke_cluster_name or not row.gke_region:
            return None
        provider = self._gcp_provider()
        if isinstance(provider, FakeGCPProvider):
            return HardwareSnapshot(cpu_utilization=0.35, memory_utilization=0.25)
        namespace = row.k8s_namespace or _DEFAULT_K8S_NAMESPACE
        label = row.k8s_pod_label or _safe_name(row.hf_model_id)
        try:
            kubeconfig = await provider.get_kube_config(
                project_id=row.gcp_project_id,
                cluster_name=row.gke_cluster_name,
                region=row.gke_region,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not refresh kubeconfig for %s: %s", row.id, exc)
            return None
        from . import kube_client

        usage = await kube_client.get_pod_resource_usage(
            kubeconfig,
            namespace=namespace,
            pod_label=label,
        )
        if usage is None:
            return None
        cpu_cores, memory_bytes = usage
        cpu_util = min(cpu_cores / _CPU_LIMIT_CORES, 1.0)
        mem_util = min(memory_bytes / _CPU_MEMORY_LIMIT_BYTES, 1.0)
        return HardwareSnapshot(cpu_utilization=cpu_util, memory_utilization=mem_util)

    def _gcp_provider(self) -> GCPProvider:
        if self._gcp_provider_factory is not None:
            return self._gcp_provider_factory()
        from ..api.dependencies import get_gcp_provider

        return get_gcp_provider()

    def _lightning_provider(self) -> LightningAIProvider:
        if self._lightning_ai_provider_factory is not None:
            return self._lightning_ai_provider_factory()
        from ..api.dependencies import get_lightning_ai_provider

        return get_lightning_ai_provider()


hardware_metrics_collector = HardwareMetricsCollector()

__all__ = [
    "HardwareMetricsCollector",
    "HardwareSnapshot",
    "hardware_metrics_collector",
    "HARDWARE_POLL_INTERVAL_SECONDS",
]
