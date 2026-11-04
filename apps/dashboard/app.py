"""
apps.dashboard.app
==================
Streamlit replay dashboard for Sentinel (Tier 6 extended objective, T6.1).

Panels (stubbed):
  • Power subsystem
  • Thermal subsystem
  • Attitude subsystem
  • Communications subsystem
  • Coordinator / fusion view

Status: scaffolding, implementation not started.
        This file is part of Tier 6 and will only be developed
        after Tier 4 evaluation results exist.
"""

from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Sentinel Replay Dashboard", layout="wide")
    st.title("🛰 Sentinel — Telemetry Replay Dashboard")
    st.warning(
        "**Status: scaffolding, implementation not started.** "
        "This dashboard is a Tier 6 extended objective (T6.1)."
    )

    tabs = st.tabs(["Power", "Thermal", "Attitude", "Communications", "Coordinator"])
    for tab, subsystem in zip(
        tabs, ["Power", "Thermal", "Attitude", "Communications", "Coordinator"]
    ):
        with tab:
            st.info(f"**{subsystem}** panel — not yet implemented (T6.1).")


if __name__ == "__main__":
    main()
