"""
tests.unit.test_adapter
=======================
Unit tests for services.data_plane.adapter (Task T0.7).

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.7)
Status:  complete — validates chronological streaming and window parameters.
"""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from libs.contracts import Subsystem, TelemetryWindow
from services.data_plane.adapter import stream_synthetic_windows, stream_windows


def test_stream_synthetic_windows_chronological_order() -> None:
    """Verify that emitted windows are strictly increasing in start_time."""
    channels = {
        "P-1": [float(i) for i in range(250)],
        "P-2": [float(i * 2) for i in range(250)],
    }
    windows = list(
        stream_synthetic_windows(
            channels=channels,
            subsystem=Subsystem.POWER,
            window_size=50,
            stride=20,
        )
    )
    assert len(windows) > 1

    # Check strict chronological ordering
    for i in range(len(windows) - 1):
        assert windows[i].start_time < windows[i + 1].start_time
        assert windows[i].end_time < windows[i + 1].end_time
        assert windows[i].window_length == 50


def test_stream_csv_windows() -> None:
    """Test streaming from a temporary CSV file."""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as tf:
        writer = csv.writer(tf)
        writer.writerow(["time", "P-1", "P-2"])
        for i in range(120):
            writer.writerow([i, float(i), float(i * 1.5)])
        csv_path = Path(tf.name)

    try:
        windows = list(
            stream_windows(
                source_path=csv_path,
                subsystem="power",
                window_size=40,
                stride=10,
            )
        )
        assert len(windows) == 9  # (120 - 40) // 10 + 1 = 9
        first = windows[0]
        assert isinstance(first, TelemetryWindow)
        assert first.subsystem == Subsystem.POWER
        assert first.window_length == 40
        assert "P-1" in first.channels
    finally:
        csv_path.unlink(missing_ok=True)


def test_stream_windows_insufficient_length() -> None:
    """Test that a series shorter than window_size emits 0 windows."""
    channels = {"P-1": [1.0, 2.0, 3.0]}
    windows = list(
        stream_synthetic_windows(
            channels=channels,
            subsystem="power",
            window_size=10,
        )
    )
    assert len(windows) == 0


def test_stream_windows_invalid_args() -> None:
    """Negative stride or window_size should raise ValueError."""
    channels = {"P-1": [1.0, 2.0]}
    with pytest.raises(ValueError):
        list(stream_synthetic_windows(channels, "power", window_size=-1))
    with pytest.raises(ValueError):
        list(stream_synthetic_windows(channels, "power", stride=0))
