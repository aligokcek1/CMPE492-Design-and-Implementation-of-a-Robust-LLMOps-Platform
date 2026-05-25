"""Fleet health summary metrics for the Deployments tab."""

from __future__ import annotations

import streamlit as st

from src.ui.fleet_counts import FleetCounts


def render_fleet_overview(counts: FleetCounts) -> None:
    """Render fleet health as a distinct summary panel (separate from deployment cards)."""
    with st.container(border=True):
        st.markdown("#### Fleet health")
        st.caption("Counts for deployments shown below. Deleted deployments are not included.")
        col_active, col_prov, col_failed = st.columns(3)
        with col_active:
            st.metric("Active", counts.active, help="Deployments in running state")
        with col_prov:
            st.metric(
                "Provisioning",
                counts.provisioning,
                help="Queued, deploying, or deleting",
            )
        with col_failed:
            st.metric("Failed", counts.failed, help="Failed or lost deployments")
