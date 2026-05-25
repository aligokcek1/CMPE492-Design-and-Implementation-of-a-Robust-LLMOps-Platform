"""Unit tests for platform hardware metrics collector."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.db import get_session_factory
from src.db.models import DeploymentRow
from src.services.gcp_fake_provider import FakeGCPProvider
from src.services.hardware_metrics_collector import HardwareMetricsCollector
from src.services.lightning_ai_fake_provider import FakeLightningAIProvider
from src.services.lightning_ai_provider import LightningSystemMetrics
from src.services.metrics_recorder import (
    HARDWARE_CPU_UTILIZATION,
    HARDWARE_GPU_UTILIZATION,
    HARDWARE_MEMORY_UTILIZATION,
)


def _seed_cpu_deployment(user_id: str = "test_user") -> str:
    dep_id = str(uuid.uuid4())
    session_factory = get_session_factory()
    with session_factory() as db:
        db.add(
            DeploymentRow(
                id=dep_id,
                user_id=user_id,
                hf_model_id="Qwen/Qwen3-1.7B",
                hf_model_display_name="Qwen3 1.7B",
                hardware_type="cpu",
                gcp_project_id=f"llmops-{dep_id.replace('-', '')[:12]}",
                gke_cluster_name="llmops-cluster",
                gke_region="us-central1",
                k8s_namespace="default",
                k8s_pod_label="qwen-qwen3-1-7b",
                status="running",
                endpoint_url="http://1.2.3.4:80",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        db.commit()
    return dep_id


def _seed_gpu_deployment(user_id: str = "test_user") -> str:
    dep_id = str(uuid.uuid4())
    session_factory = get_session_factory()
    with session_factory() as db:
        db.add(
            DeploymentRow(
                id=dep_id,
                user_id=user_id,
                hf_model_id="Qwen/Qwen3-1.7B",
                hf_model_display_name="Qwen3 1.7B",
                hardware_type="gpu",
                lightning_ai_deployment_id=f"lai-{dep_id[:8]}",
                lightning_teamspace_id="teamspace-123",
                lightning_deployment_uuid=f"uuid-{dep_id[:8]}",
                status="running",
                endpoint_url="https://fake.lightning.ai",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        db.commit()
    return dep_id


@pytest.mark.asyncio
async def test_collector_records_cpu_hardware_from_fake_gke(temp_db, monkeypatch):
    monkeypatch.delenv("LLMOPS_METRICS_DISABLED", raising=False)
    dep_id = _seed_cpu_deployment()
    fake_gcp = FakeGCPProvider()
    collector = HardwareMetricsCollector(gcp_provider_factory=lambda: fake_gcp)

    await collector.poll_running_deployments()

    samples = (
        HARDWARE_CPU_UTILIZATION.labels(
            deployment_id=dep_id, user_id="test_user", hardware_type="cpu"
        )
        .collect()[0]
        .samples
    )
    assert samples[0].value == pytest.approx(0.35)


@pytest.mark.asyncio
async def test_collector_records_gpu_hardware_from_lightning(temp_db, monkeypatch):
    monkeypatch.delenv("LLMOPS_METRICS_DISABLED", raising=False)
    dep_id = _seed_gpu_deployment()
    fake_lightning = FakeLightningAIProvider()
    fake_lightning.system_metrics = LightningSystemMetrics(
        cpu_utilization=0.1,
        memory_utilization=0.45,
        gpu_utilization=0.72,
    )

    from src.services import lightning_ai_credentials_store as creds_mod

    async def _fake_creds(*, user_id: str):
        from src.services.lightning_ai_credentials_store import LightningAICredentials

        return LightningAICredentials(api_key="fake-key", lightning_user_id="user-uuid")

    monkeypatch.setattr(creds_mod.lightning_ai_credentials_store, "get_credentials", _fake_creds)

    collector = HardwareMetricsCollector(lightning_ai_provider_factory=lambda: fake_lightning)
    await collector.poll_running_deployments()

    cpu_samples = (
        HARDWARE_CPU_UTILIZATION.labels(
            deployment_id=dep_id, user_id="test_user", hardware_type="gpu"
        )
        .collect()[0]
        .samples
    )
    assert cpu_samples[0].value == pytest.approx(0.1)

    gpu_samples = (
        HARDWARE_GPU_UTILIZATION.labels(
            deployment_id=dep_id, user_id="test_user", hardware_type="gpu"
        )
        .collect()[0]
        .samples
    )
    assert gpu_samples[0].value == pytest.approx(0.72)

    mem_samples = (
        HARDWARE_MEMORY_UTILIZATION.labels(
            deployment_id=dep_id, user_id="test_user", hardware_type="gpu"
        )
        .collect()[0]
        .samples
    )
    assert mem_samples[0].value == pytest.approx(0.45)
