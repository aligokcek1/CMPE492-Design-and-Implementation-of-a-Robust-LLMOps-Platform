"""Prometheus metric instrumentation for inference proxy traffic."""
from __future__ import annotations

import os

from prometheus_client import Counter, Gauge, Histogram


def _metrics_disabled() -> bool:
    return os.environ.get("LLMOPS_METRICS_DISABLED") == "1"


_LABELS = ("deployment_id", "user_id", "hardware_type")
_OUTCOME_LABELS = ("deployment_id", "user_id", "hardware_type", "outcome")

TTFT_SECONDS = Histogram(
    "llmops_ttft_seconds",
    "Time to first response byte for inference requests",
    _LABELS,
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

TOKENS_TOTAL = Counter(
    "llmops_tokens_total",
    "Total output tokens counted from inference responses",
    _LABELS,
)

INFERENCE_REQUESTS_TOTAL = Counter(
    "llmops_inference_requests_total",
    "Inference request outcomes",
    _OUTCOME_LABELS,
)

HARDWARE_CPU_UTILIZATION = Gauge(
    "llmops_hardware_cpu_utilization",
    "CPU utilization ratio (0-1): pod/limit on CPU deployments, host CPU on GPU",
    _LABELS,
)

HARDWARE_MEMORY_UTILIZATION = Gauge(
    "llmops_hardware_memory_utilization",
    "Memory utilization ratio (0-1): pod RAM/limit on CPU, GPU VRAM/total on GPU",
    _LABELS,
)

HARDWARE_GPU_UTILIZATION = Gauge(
    "llmops_hardware_gpu_utilization",
    "GPU utilization ratio (0-1)",
    _LABELS,
)


def record_success(
    *,
    deployment_id: str,
    user_id: str,
    hardware_type: str,
    ttft_seconds: float,
    token_count: int,
) -> None:
    if _metrics_disabled():
        return
    if token_count <= 0:
        record_outcome(
            deployment_id=deployment_id,
            user_id=user_id,
            hardware_type=hardware_type,
            outcome="no_token",
        )
        return
    TTFT_SECONDS.labels(
        deployment_id=deployment_id,
        user_id=user_id,
        hardware_type=hardware_type,
    ).observe(ttft_seconds)
    TOKENS_TOTAL.labels(
        deployment_id=deployment_id,
        user_id=user_id,
        hardware_type=hardware_type,
    ).inc(token_count)
    record_outcome(
        deployment_id=deployment_id,
        user_id=user_id,
        hardware_type=hardware_type,
        outcome="success",
    )


def record_hardware_metrics(
    *,
    deployment_id: str,
    user_id: str,
    hardware_type: str,
    cpu_utilization: float | None = None,
    memory_utilization: float | None = None,
    gpu_utilization: float | None = None,
) -> None:
    if _metrics_disabled():
        return
    labels = {
        "deployment_id": deployment_id,
        "user_id": user_id,
        "hardware_type": hardware_type,
    }
    if cpu_utilization is not None:
        HARDWARE_CPU_UTILIZATION.labels(**labels).set(cpu_utilization)
    if memory_utilization is not None:
        HARDWARE_MEMORY_UTILIZATION.labels(**labels).set(memory_utilization)
    if gpu_utilization is not None:
        HARDWARE_GPU_UTILIZATION.labels(**labels).set(gpu_utilization)


def record_outcome(
    *,
    deployment_id: str,
    user_id: str,
    hardware_type: str,
    outcome: str,
) -> None:
    if _metrics_disabled():
        return
    INFERENCE_REQUESTS_TOTAL.labels(
        deployment_id=deployment_id,
        user_id=user_id,
        hardware_type=hardware_type,
        outcome=outcome,
    ).inc()


__all__ = [
    "TTFT_SECONDS",
    "TOKENS_TOTAL",
    "INFERENCE_REQUESTS_TOTAL",
    "HARDWARE_CPU_UTILIZATION",
    "HARDWARE_MEMORY_UTILIZATION",
    "HARDWARE_GPU_UTILIZATION",
    "record_success",
    "record_hardware_metrics",
    "record_outcome",
]
