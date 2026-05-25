"""Emoji-free deployment status presentation."""

from __future__ import annotations

import streamlit as st

_STATUS_LABELS: dict[str, str] = {
    "queued": "Queued",
    "deploying": "Deploying",
    "running": "Running",
    "failed": "Failed",
    "deleting": "Deleting",
    "deleted": "Deleted",
    "lost": "Lost",
}

_BADGE_COLORS: dict[str, str] = {
    "queued": "orange",
    "deploying": "orange",
    "deleting": "orange",
    "running": "green",
    "failed": "red",
    "lost": "red",
    "deleted": "gray",
}


def status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status.replace("_", " ").title())


def render_status_badge(status: str) -> None:
    """Render a color-coded status indicator without emoji (FR-010)."""
    label = status_label(status)
    color = _BADGE_COLORS.get(status, "gray")
    st.badge(label, color=color)
