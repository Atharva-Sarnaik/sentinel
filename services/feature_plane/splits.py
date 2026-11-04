"""
services.feature_plane.splits
================================
Chronological train/test split with boundary enforcement.

Design rule (ADR-0002):
  • Splits are strictly chronological — NO random shuffling.
  • The boundary is logged and reproducible given the same config.
  • The leakage regression suite (T0.10) catches any shuffle bug.

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import TelemetryWindow


def chronological_split(
    windows: list[TelemetryWindow],
    test_fraction: float = 0.2,
) -> tuple[list[TelemetryWindow], list[TelemetryWindow]]:
    """
    Split windows into (train, test) in strict chronological order.

    Args:
        windows:       List of TelemetryWindows sorted by start_time ascending.
        test_fraction: Fraction of windows reserved for the test set.

    Returns:
        (train_windows, test_windows)

    Raises:
        NotImplementedError: Implementation pending task T0.9.
    """
    # TODO (T0.9): implement chronological split.
    raise NotImplementedError("chronological_split: implementation pending task T0.9.")
