"""Unit tests for fleet overview counting and visibility filter."""

from __future__ import annotations

from src.ui.fleet_counts import compute_fleet_counts, filter_visible_deployments


def _dep(status: str, dep_id: str = "x") -> dict:
    return {"id": dep_id, "status": status, "hf_model_id": "org/m"}


def test_active_running_only():
    counts = compute_fleet_counts([_dep("running"), _dep("running", "b")])
    assert counts.active == 2
    assert counts.provisioning == 0
    assert counts.failed == 0


def test_provisioning_includes_queued_deploying_deleting():
    counts = compute_fleet_counts(
        [
            _dep("queued"),
            _dep("deploying"),
            _dep("deleting"),
        ]
    )
    assert counts.provisioning == 3
    assert counts.active == 0


def test_failed_includes_failed_and_lost():
    counts = compute_fleet_counts([_dep("failed"), _dep("lost")])
    assert counts.failed == 2


def test_deleted_excluded_from_all_buckets():
    counts = compute_fleet_counts(
        [
            _dep("deleted"),
            _dep("running"),
            _dep("failed"),
        ]
    )
    assert counts.active == 1
    assert counts.failed == 1
    assert counts.provisioning == 0


def test_filter_always_hides_deleted():
    deps = [_dep("running"), _dep("deleted", "d2")]
    visible = filter_visible_deployments(deps)
    assert len(visible) == 1
    assert visible[0]["status"] == "running"
