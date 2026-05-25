"""Fleet overview counting and deployment list visibility filtering."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FleetCounts:
    active: int
    provisioning: int
    failed: int


_PROVISIONING = frozenset({"queued", "deploying", "deleting"})
_FAILED = frozenset({"failed", "lost"})


def filter_visible_deployments(deployments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return deployments for list rendering; always exclude deleted rows."""
    return [d for d in deployments if d.get("status") != "deleted"]


def compute_fleet_counts(deployments: list[dict[str, Any]]) -> FleetCounts:
    """Aggregate fleet metrics; deleted rows never affect buckets (FR-003)."""
    active = provisioning = failed = 0
    for dep in deployments:
        status = dep.get("status", "")
        if status == "deleted":
            continue
        if status == "running":
            active += 1
        elif status in _PROVISIONING:
            provisioning += 1
        elif status in _FAILED:
            failed += 1
    return FleetCounts(active=active, provisioning=provisioning, failed=failed)
