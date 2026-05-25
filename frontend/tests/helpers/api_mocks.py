"""Shared HTTP mocks for Streamlit AppTest integration tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

_UNCONFIGURED_CREDS: dict[str, Any] = {"configured": False}

_DEFAULT_METRICS: dict[str, Any] = {
    "deployment_id": "dep-metrics-001",
    "hardware_type": "cpu",
    "platform_label": "GKE / TGI",
    "range": "1h",
    "summary": {
        "ttft_avg_seconds": 0.5,
        "ttft_p95_seconds": 1.0,
        "throughput_value": 10.0,
        "throughput_unit": "tokens_per_second",
        "failed_requests_excluded": False,
    },
    "series": {"ttft": [], "throughput": [], "hardware": {}},
    "empty": False,
}


def mock_json_response(
    data: Any,
    *,
    ok: bool = True,
    status_code: int = 200,
) -> MagicMock:
    resp = MagicMock(ok=ok, status_code=status_code)
    resp.json.return_value = data
    resp.text = str(data)
    return resp


def make_get_side_effect(
    *,
    deployments: list[dict[str, Any]] | None = None,
    gcp: dict[str, Any] | None = None,
    lightning: dict[str, Any] | None = None,
    models: list[dict[str, Any]] | None = None,
    session: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    handler: Callable[..., MagicMock | None] | None = None,
) -> Callable[..., MagicMock]:
    """Route ``requests.get`` by URL for authenticated app runs."""

    def _get(url: str, *args: Any, **kwargs: Any) -> MagicMock:
        if handler is not None:
            custom = handler(url, *args, **kwargs)
            if custom is not None:
                return custom

        if "/api/auth/session" in url:
            if session is not None:
                return mock_json_response(session)
            return mock_json_response(
                {"detail": "Unauthorized"},
                ok=False,
                status_code=401,
            )
        if url.rstrip("/").endswith("/api/deployments"):
            return mock_json_response(deployments if deployments is not None else [])
        if "/api/deployments/" in url and "/metrics" in url and "grafana" not in url:
            return mock_json_response(metrics if metrics is not None else _DEFAULT_METRICS)
        if "/metrics/grafana" in url:
            return mock_json_response(
                {
                    "redirect_url": (
                        "http://localhost:8000/api/metrics/grafana/redirect?token=signed"
                    ),
                    "expires_at": "2099-01-01T00:00:00Z",
                }
            )
        if "/api/gcp/credentials" in url:
            return mock_json_response(gcp if gcp is not None else _UNCONFIGURED_CREDS)
        if "/api/lightning/credentials" in url:
            return mock_json_response(lightning if lightning is not None else _UNCONFIGURED_CREDS)
        if "/api/models/public" in url:
            return mock_json_response({})
        if url.rstrip("/").endswith("/api/models"):
            return mock_json_response(models if models is not None else [])
        return mock_json_response({})

    return _get
