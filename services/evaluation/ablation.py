"""
services.evaluation.ablation
==============================
Ablation harness — runs all five evaluation arms on identical windows.

Arms:
  A — Static threshold baseline
  B — Isolation Forest baseline
  C — Single combined LSTM-AE
  D — Specialist agents (no coordinator)
  E — Full coordinated system (Sentinel)

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    4 (task T4.2)
Status:  not started
"""

from __future__ import annotations

from typing import Any

ARMS = ("A", "B", "C", "D", "E")


def run_ablation(
    windows: list[Any],
    arms: tuple[str, ...] = ARMS,
) -> dict[str, dict[str, float]]:
    """
    Run each arm on the same windows and return a metrics dict.

    Args:
        windows: Identical list of TelemetryWindows for all arms.
        arms:    Subset of arms to run (default: all five).

    Returns:
        dict[arm_label -> metrics_dict]

    Raises:
        NotImplementedError: Implementation pending task T4.2.
    """
    # TODO (T4.2): implement ablation harness.
    raise NotImplementedError("run_ablation: implementation pending task T4.2.")
