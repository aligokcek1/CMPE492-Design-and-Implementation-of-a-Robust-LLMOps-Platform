"""Integration tests for the refactored Deployments dashboard (feature 011)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from tests.helpers.api_mocks import make_get_side_effect, mock_json_response

APP_MODULE = "src/app.py"


def _val(el) -> str:
    if hasattr(el, "value"):
        return str(el.value)
    return str(el)


def _all_text(at: AppTest) -> str:
    parts: list[str] = []
    for m in at.metric:
        if getattr(m, "label", None):
            parts.append(str(m.label))
        parts.append(_val(m))
    for c in at.code:
        parts.append(_val(c))
    for cb in at.checkbox:
        if getattr(cb, "label", None):
            parts.append(str(cb.label))
    for group in (
        at.markdown,
        at.text,
        at.title,
        at.subheader,
        at.caption,
        at.info,
        at.error,
        at.warning,
        at.button,
    ):
        for el in group:
            parts.append(_val(el))
    return " ".join(parts)


@pytest.fixture
def authed_at():
    at = AppTest.from_file(APP_MODULE, default_timeout=30)
    at.session_state["session_token"] = "session_abc"
    at.session_state["hf_username"] = "alice"
    at.session_state["_session_checked"] = True
    return at


def _deployments_payload():
    return [
        {
            "id": "dep-run",
            "hf_model_id": "org/running",
            "hf_model_display_name": "Running Model",
            "hardware_type": "cpu",
            "model_origin": "public",
            "status": "running",
            "status_message": "Ready",
            "endpoint_url": "http://10.0.0.1:8080",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": "dep-del",
            "hf_model_id": "org/deleted",
            "hardware_type": "cpu",
            "model_origin": "public",
            "status": "deleted",
            "status_message": "Removed",
            "endpoint_url": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": "dep-fail",
            "hf_model_id": "org/failed",
            "hardware_type": "gpu",
            "model_origin": "public",
            "status": "failed",
            "status_message": "Provisioning failed",
            "endpoint_url": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    ]


def test_four_tabs_deployments_first_no_emoji(authed_at):
    authed_at.run()
    assert not authed_at.exception
    labels = [t.label for t in authed_at.tabs]
    assert labels == ["Deployments", "Upload Model", "Select Model", "Deploy"]
    assert labels[0] == "Deployments"


def test_fleet_metrics_labels_and_counts(authed_at):
    deps = _deployments_payload()
    with patch(
        "src.services.api_client.requests.get",
        side_effect=make_get_side_effect(deployments=deps),
    ):
        authed_at.run()

    assert not authed_at.exception
    text = _all_text(authed_at)
    assert "Active" in text
    assert "Provisioning" in text
    assert "Failed" in text
    metric_values = {_val(m) for m in authed_at.metric}
    assert "1" in metric_values or any("1" in _val(m) for m in authed_at.metric)


def test_empty_deployments_professional_copy(authed_at):
    with patch(
        "src.services.api_client.requests.get",
        side_effect=make_get_side_effect(deployments=[]),
    ):
        authed_at.run()

    text = _all_text(authed_at)
    assert "No deployments yet" in text
    assert "Deploy" in text


def test_deleted_deployments_hidden_from_list(authed_at):
    deps = _deployments_payload()
    with patch(
        "src.services.api_client.requests.get",
        side_effect=make_get_side_effect(deployments=deps),
    ):
        authed_at.run()

    text = _all_text(authed_at)
    assert "org/deleted" not in text
    assert "org/running" in text


def test_list_fetch_error_professional_message(authed_at):
    fail = mock_json_response({"detail": "Service unavailable"}, ok=False, status_code=503)

    def _get(url, *args, **kwargs):
        if url.rstrip("/").endswith("/api/deployments"):
            return fail
        return make_get_side_effect()(url, *args, **kwargs)

    with patch("src.services.api_client.requests.get", side_effect=_get):
        authed_at.run()

    assert any("Service unavailable" in _val(e) for e in authed_at.error)


def test_collapsed_row_no_metrics_button(authed_at):
    deps = [_deployments_payload()[0]]
    with patch(
        "src.services.api_client.requests.get",
        side_effect=make_get_side_effect(deployments=deps),
    ):
        authed_at.run()

    text = _all_text(authed_at)
    assert "http://10.0.0.1:8080" in text
    assert "Open in Grafana" not in text
    assert any("Details" in e.label for e in authed_at.expander)
