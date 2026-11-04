"""
services.data_plane.adapter
============================
NASA SMAP / MSL telemetry replay adapter.

Fallback datasets: ESA-ADB, OPS-SAT (see ADR-0001).

Inputs:  raw telemetry files from data/raw/ (DVC-tracked, gitignored)
Outputs: libs.contracts.TelemetryWindow (one per subsystem per window)

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.7)
Status:  not started
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from libs.contracts import TelemetryWindow


def stream_windows(
    source_path: Path,
    subsystem: str,
    window_size: int = 100,
    stride: int = 10,
) -> Iterator[TelemetryWindow]:
    """
    Stream telemetry windows from a replay source in chronological order.

    Design rule (ADR-0002): windows must be emitted in time order.
    No shuffling. No future data exposed to earlier windows.

    Args:
        source_path: Path to the raw telemetry file or directory.
        subsystem:   Target subsystem name (e.g. 'power').
        window_size: Number of time steps per window.
        stride:      Step size between consecutive windows.

    Yields:
        TelemetryWindow objects, ordered by start_time ascending.

    Raises:
        NotImplementedError: Implementation pending task T0.7.
    """
    # TODO (T0.7): implement SMAP/MSL adapter with chronological streaming.
    raise NotImplementedError("stream_windows: implementation pending task T0.7.")
