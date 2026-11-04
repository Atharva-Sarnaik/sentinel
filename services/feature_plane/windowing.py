"""
services.feature_plane.windowing
==================================
Sliding-window extraction over raw telemetry time series.

Inputs:  streaming TelemetryWindow objects from data_plane.adapter
Outputs: feature-ready TelemetryWindow with normalised channels

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import TelemetryWindow


def apply_sliding_window(
    window: TelemetryWindow,
    window_size: int,
    stride: int,
) -> list[TelemetryWindow]:
    """
    Slice a TelemetryWindow into sub-windows of fixed size.

    Raises:
        NotImplementedError: Implementation pending task T0.9.
    """
    # TODO (T0.9): implement sliding window extraction.
    raise NotImplementedError("apply_sliding_window: implementation pending task T0.9.")
