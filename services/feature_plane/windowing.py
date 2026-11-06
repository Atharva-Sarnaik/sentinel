"""
services.feature_plane.windowing
==================================
Sliding-window extraction over raw telemetry time series.

Inputs:  streaming TelemetryWindow objects from data_plane.adapter
Outputs: feature-ready TelemetryWindow with normalised channels

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  complete — sliding window sub-slicer.
"""

from __future__ import annotations

from datetime import timedelta

from libs.contracts import TelemetryWindow


def apply_sliding_window(
    window: TelemetryWindow,
    window_size: int,
    stride: int,
) -> list[TelemetryWindow]:
    """
    Slice a larger TelemetryWindow into smaller sub-windows of fixed size.

    Args:
        window: Input TelemetryWindow.
        window_size: Number of time steps per sub-window.
        stride: Step size between consecutive sub-windows.

    Returns:
        List of sub-sliced TelemetryWindows.
    """
    total_len = window.window_length
    if total_len < window_size or window_size <= 0 or stride <= 0:
        return []

    sub_windows: list[TelemetryWindow] = []
    # Calculate approx interval per step
    total_seconds = (window.end_time - window.start_time).total_seconds()
    dt = total_seconds / max(1, total_len - 1)

    for start_idx in range(0, total_len - window_size + 1, stride):
        end_idx = start_idx + window_size
        sub_channels = {ch: series[start_idx:end_idx] for ch, series in window.channels.items()}
        sub_start_time = window.start_time + timedelta(seconds=start_idx * dt)
        sub_end_time = window.start_time + timedelta(seconds=(end_idx - 1) * dt)

        sub_windows.append(
            TelemetryWindow(
                subsystem=window.subsystem,
                start_time=sub_start_time,
                end_time=sub_end_time,
                channels=sub_channels,
                source_dataset=window.source_dataset,
                metadata={**window.metadata, "sub_window": True, "start_index": start_idx},
            )
        )

    return sub_windows
