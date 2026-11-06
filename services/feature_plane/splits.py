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
Status:  complete — strictly chronological window split.
"""

from __future__ import annotations

import math

from libs.common.helpers import assert_no_future_leakage
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
        ValueError: If test_fraction not in (0, 1).
    """
    if not (0.0 < test_fraction < 1.0):
        raise ValueError(f"test_fraction must be in (0, 1), got {test_fraction}")

    n = len(windows)
    if n == 0:
        return [], []

    # Sort windows by start_time to guarantee ordering
    sorted_windows = sorted(windows, key=lambda w: w.start_time)
    split_idx = math.floor((1.0 - test_fraction) * n)

    train_windows = sorted_windows[:split_idx]
    test_windows = sorted_windows[split_idx:]

    # Assert no future leakage across boundary
    if train_windows and test_windows:
        assert_no_future_leakage(
            [w.end_time for w in train_windows],
            [w.start_time for w in test_windows],
        )

    return train_windows, test_windows
