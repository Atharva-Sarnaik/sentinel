"""
services.data_plane.adapter
============================
NASA SMAP / MSL telemetry replay adapter.

Fallback datasets: ESA-ADB, OPS-SAT (see ADR-0001).

Inputs:  raw telemetry files from data/raw/ (DVC-tracked, gitignored)
Outputs: libs.contracts.TelemetryWindow (one per subsystem per window)

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.7)
Status:  complete — streams chronological TelemetryWindows with no future leakage.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

from libs.contracts import Subsystem, TelemetryWindow


def stream_windows(
    source_path: Path,
    subsystem: Subsystem | str,
    window_size: int = 100,
    stride: int = 10,
    base_timestamp: datetime | None = None,
    time_step_seconds: float = 1.0,
) -> Iterator[TelemetryWindow]:
    """
    Stream telemetry windows from a replay source in chronological order.

    Design rule (ADR-0002): windows must be emitted in time order.
    No shuffling. No future data exposed to earlier windows.

    Args:
        source_path: Path to the raw telemetry file (.csv or tabular) or directory.
        subsystem:   Target subsystem name (e.g. Subsystem.POWER or 'power').
        window_size: Number of time steps per window.
        stride:      Step size between consecutive windows.
        base_timestamp: Starting datetime for synthetic/inferred timestamps (defaults to 2024-01-01 UTC).
        time_step_seconds: Interval in seconds between sequential samples.

    Yields:
        TelemetryWindow objects, ordered strictly by start_time ascending.

    Raises:
        FileNotFoundError: If source_path does not exist.
        ValueError: If window_size <= 0 or stride <= 0.
    """
    if window_size <= 0:
        raise ValueError(f"window_size must be positive, got {window_size}")
    if stride <= 0:
        raise ValueError(f"stride must be positive, got {stride}")

    if not source_path.exists():
        raise FileNotFoundError(f"Telemetry source path not found: {source_path}")

    subsystem_enum = Subsystem(str(subsystem).lower())
    t0 = base_timestamp or datetime(2024, 1, 1, 0, 0, tzinfo=UTC)

    # Ingest raw channel data from CSV file
    channel_data: dict[str, list[float]] = {}
    with source_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            for col in reader.fieldnames:
                if col.lower() not in ("timestamp", "time", "index"):
                    channel_data[col] = []

            for row in reader:
                for col in channel_data:
                    val_str = row.get(col, "0.0")
                    try:
                        channel_data[col].append(float(val_str) if val_str else 0.0)
                    except ValueError:
                        channel_data[col].append(0.0)

    total_steps = len(next(iter(channel_data.values()))) if channel_data else 0

    if total_steps < window_size:
        return

    # Slice windows chronologically
    for start_idx in range(0, total_steps - window_size + 1, stride):
        end_idx = start_idx + window_size
        start_time = t0 + timedelta(seconds=start_idx * time_step_seconds)
        end_time = t0 + timedelta(seconds=(end_idx - 1) * time_step_seconds)

        window_channels = {ch: series[start_idx:end_idx] for ch, series in channel_data.items()}

        yield TelemetryWindow(
            subsystem=subsystem_enum,
            start_time=start_time,
            end_time=end_time,
            channels=window_channels,
            source_dataset=source_path.stem.upper(),
            metadata={
                "source_file": source_path.name,
                "start_index": start_idx,
                "end_index": end_idx,
            },
        )


def stream_synthetic_windows(
    channels: dict[str, list[float]],
    subsystem: Subsystem | str,
    window_size: int = 100,
    stride: int = 10,
    base_timestamp: datetime | None = None,
    time_step_seconds: float = 1.0,
    source_name: str = "SYNTHETIC",
) -> Iterator[TelemetryWindow]:
    """
    In-memory generator streaming TelemetryWindows for testing and quick verification.
    """
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if stride <= 0:
        raise ValueError("stride must be positive")

    subsystem_enum = Subsystem(str(subsystem).lower())
    t0 = base_timestamp or datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    total_steps = len(next(iter(channels.values()))) if channels else 0

    if total_steps < window_size:
        return

    for start_idx in range(0, total_steps - window_size + 1, stride):
        end_idx = start_idx + window_size
        start_time = t0 + timedelta(seconds=start_idx * time_step_seconds)
        end_time = t0 + timedelta(seconds=(end_idx - 1) * time_step_seconds)

        window_channels = {ch: series[start_idx:end_idx] for ch, series in channels.items()}

        yield TelemetryWindow(
            subsystem=subsystem_enum,
            start_time=start_time,
            end_time=end_time,
            channels=window_channels,
            source_dataset=source_name,
            metadata={"start_index": start_idx, "end_index": end_idx},
        )
