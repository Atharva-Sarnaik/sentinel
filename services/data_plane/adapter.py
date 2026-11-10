"""
services.data_plane.adapter
============================
NASA SMAP / MSL telemetry replay adapter.

Fallback datasets: ESA-ADB, OPS-SAT (see ADR-0001).

Inputs:  raw telemetry files from data/raw/ (DVC-tracked, gitignored)
Outputs: libs.contracts.TelemetryWindow (one per subsystem per window)

Supported formats:
  • CSV   — via ``stream_windows()``  (original)
  • .npy  — via ``stream_npy_windows()``  (single-channel SMAP/MSL)
  • .npy  — via ``stream_npy_multi_channel_windows()``  (multi-channel merge)
  • dict  — via ``stream_synthetic_windows()``  (in-memory / tests)

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.7)
Status:  complete — streams chronological TelemetryWindows with no future leakage.
"""

from __future__ import annotations

import ast
import csv
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

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


# ---------------------------------------------------------------------------
# SMAP / MSL anomaly label loader
# ---------------------------------------------------------------------------


def load_smap_labels(
    labels_csv: Path,
    chan_id: str,
    spacecraft: str = "SMAP",
) -> list[tuple[int, int]]:
    """
    Parse ``labeled_anomalies.csv`` and return anomaly index intervals for a channel.

    **Convention (Hundman et al., KDD 2018):**
    Both ``start`` and ``end`` in each ``[start, end]`` pair are **inclusive**
    indices into the test ``.npy`` array.  This function returns them as-is;
    callers that need half-open ranges must add 1 to the end.

    Args:
        labels_csv: Path to ``labeled_anomalies.csv`` from the SMAP/MSL dataset.
        chan_id:     Channel identifier matching the ``.npy`` filename (e.g. ``"P-1"``).
        spacecraft: ``"SMAP"`` or ``"MSL"``.

    Returns:
        List of ``(start_idx, end_idx)`` tuples (both inclusive).
        Empty list if the channel has no anomalies or is not present.

    Raises:
        FileNotFoundError: If *labels_csv* does not exist.
    """
    if not labels_csv.exists():
        raise FileNotFoundError(f"Labels CSV not found: {labels_csv}")

    intervals: list[tuple[int, int]] = []
    with labels_csv.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("chan_id") == chan_id and row.get("spacecraft") == spacecraft:
                raw = row.get("anomaly_sequences", "[]")
                for seq in ast.literal_eval(raw):
                    intervals.append((int(seq[0]), int(seq[1])))
    return intervals


# ---------------------------------------------------------------------------
# Helper: check whether a window [w_start, w_end) overlaps any inclusive
# anomaly interval [iv_start, iv_end].
# ---------------------------------------------------------------------------


def _window_overlaps_anomaly(
    w_start: int,
    w_end_exclusive: int,
    intervals: list[tuple[int, int]],
) -> bool:
    """Return True if window ``[w_start, w_end_exclusive)`` overlaps any
    **inclusive** anomaly interval ``[iv_start, iv_end]``.
    """
    w_last = w_end_exclusive - 1  # last index inside the window
    return any(w_last >= iv_start and w_start <= iv_end for iv_start, iv_end in intervals)


# ---------------------------------------------------------------------------
# Single-channel .npy streaming
# ---------------------------------------------------------------------------


def stream_npy_windows(
    npy_path: Path,
    channel_name: str,
    subsystem: Subsystem | str,
    window_size: int = 100,
    stride: int = 10,
    base_timestamp: datetime | None = None,
    time_step_seconds: float = 1.0,
    label_intervals: list[tuple[int, int]] | None = None,
    source_name: str = "SMAP",
) -> Iterator[TelemetryWindow]:
    """
    Stream :class:`TelemetryWindow` objects from a NASA SMAP/MSL ``.npy`` file.

    Design rule (ADR-0002): windows are emitted in strict chronological order.
    No shuffling.  No future data exposed to earlier windows.

    The ``.npy`` file is expected to be a 2-D ``float`` array of shape
    ``(n_timesteps, n_features)``.  **Column 0** is the primary channel signal;
    remaining columns are ancillary features and are not mapped to named
    channels (they are available in metadata for downstream consumers that
    need full multivariate context).

    Args:
        npy_path:          Path to the ``.npy`` file
                           (e.g. ``data/raw/SMAP/train/P-1.npy``).
        channel_name:      Canonical SMAP channel ID (e.g. ``"P-1"``), used
                           as the key in ``TelemetryWindow.channels``.
        subsystem:         Target subsystem (``Subsystem`` enum or string).
        window_size:       Number of time steps per window.
        stride:            Step size between consecutive windows.
        base_timestamp:    Starting datetime for synthesised timestamps.
                           Defaults to ``2024-01-01 00:00 UTC``.
        time_step_seconds: Interval in seconds between sequential samples.
        label_intervals:   Optional list of ``(start_idx, end_idx)`` anomaly
                           ranges from ``labeled_anomalies.csv`` (test split
                           only).  **Both endpoints are inclusive** per the
                           Hundman et al. (KDD 2018) convention.
                           Each window's ``metadata["is_anomalous"]`` is set
                           to ``True`` if the window overlaps any interval.
        source_name:       Source dataset label written to
                           ``TelemetryWindow.source_dataset``.

    Yields:
        ``TelemetryWindow`` objects ordered strictly by ``start_time`` ascending.

    Raises:
        FileNotFoundError: If *npy_path* does not exist.
        ValueError: If *window_size* or *stride* ≤ 0, or the ``.npy`` array
                    is not 2-D, or has 0 feature columns, or contains
                    non-finite values in column 0.
    """
    if window_size <= 0:
        raise ValueError(f"window_size must be positive, got {window_size}")
    if stride <= 0:
        raise ValueError(f"stride must be positive, got {stride}")
    if not npy_path.exists():
        raise FileNotFoundError(f"NumPy telemetry file not found: {npy_path}")

    arr = np.load(npy_path)

    # ── shape validation ──────────────────────────────────────────────────
    if arr.ndim != 2:
        raise ValueError(
            f"Expected 2-D array from {npy_path}, got shape {arr.shape}. "
            f"SMAP .npy files must be (n_timesteps, n_features)."
        )
    if arr.shape[1] < 1:
        raise ValueError(f"SMAP .npy file has 0 feature columns: {npy_path}")

    # ── extract primary signal (column 0) and validate ────────────────────
    primary = arr[:, 0].astype(np.float64)
    if not np.all(np.isfinite(primary)):
        raise ValueError(
            f"Primary signal (column 0) of {npy_path} contains non-finite values (NaN or Inf)."
        )

    subsystem_enum = Subsystem(str(subsystem).lower())
    t0 = base_timestamp or datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    n_steps = arr.shape[0]
    primary_list: list[float] = primary.tolist()

    if n_steps < window_size:
        return

    intervals = label_intervals or []

    for start_idx in range(0, n_steps - window_size + 1, stride):
        end_idx = start_idx + window_size
        start_time = t0 + timedelta(seconds=start_idx * time_step_seconds)
        end_time = t0 + timedelta(seconds=(end_idx - 1) * time_step_seconds)

        is_anomalous = _window_overlaps_anomaly(start_idx, end_idx, intervals)

        yield TelemetryWindow(
            subsystem=subsystem_enum,
            start_time=start_time,
            end_time=end_time,
            channels={channel_name: primary_list[start_idx:end_idx]},
            source_dataset=source_name,
            metadata={
                "npy_file": npy_path.name,
                "start_index": start_idx,
                "end_index": end_idx,
                "is_anomalous": is_anomalous,
            },
        )


# ---------------------------------------------------------------------------
# Multi-channel .npy streaming (Option B — reusable helper)
# ---------------------------------------------------------------------------


def stream_npy_multi_channel_windows(
    channel_paths: dict[str, Path],
    subsystem: Subsystem | str,
    window_size: int = 100,
    stride: int = 10,
    base_timestamp: datetime | None = None,
    time_step_seconds: float = 1.0,
    label_intervals: list[tuple[int, int]] | None = None,
    source_name: str = "SMAP",
) -> Iterator[TelemetryWindow]:
    """
    Stream multi-channel :class:`TelemetryWindow` objects by merging several
    single-channel SMAP/MSL ``.npy`` files.

    This is the **Option B** helper: a reusable adapter for training,
    inference and dashboard replay.  It loads each channel's primary signal
    (column 0), validates that all channels have matching timestep counts,
    and yields windows containing all channels in deterministic sorted order.

    Design rule (ADR-0002): windows are emitted in strict chronological order.

    Args:
        channel_paths:     Mapping of canonical channel name → ``.npy`` file
                           path (e.g. ``{"P-1": Path("train/P-1.npy"), ...}``).
        subsystem:         Target subsystem.
        window_size:       Number of time steps per window.
        stride:            Step size between consecutive windows.
        base_timestamp:    Starting datetime for synthesised timestamps.
        time_step_seconds: Interval in seconds between sequential samples.
        label_intervals:   Optional anomaly ranges (both endpoints inclusive).
        source_name:       Source dataset label.

    Yields:
        ``TelemetryWindow`` objects with **all** channels merged, ordered
        strictly by ``start_time`` ascending.

    Raises:
        FileNotFoundError: If any ``.npy`` file does not exist.
        ValueError: If *channel_paths* is empty, if any ``.npy`` file is not
                    2-D or has < 1 column, if timestep counts differ across
                    channels, if *window_size* or *stride* ≤ 0, or if any
                    primary signal contains non-finite values.
    """
    if window_size <= 0:
        raise ValueError(f"window_size must be positive, got {window_size}")
    if stride <= 0:
        raise ValueError(f"stride must be positive, got {stride}")
    if not channel_paths:
        raise ValueError("channel_paths must be a non-empty mapping of channel name → .npy path.")

    # ── load and validate each channel ────────────────────────────────────
    channel_signals: dict[str, list[float]] = {}
    n_steps: int | None = None

    for ch_name in sorted(channel_paths):  # deterministic order
        npy_path = channel_paths[ch_name]
        if not npy_path.exists():
            raise FileNotFoundError(
                f"NumPy telemetry file not found for channel '{ch_name}': {npy_path}"
            )

        arr = np.load(npy_path)
        if arr.ndim != 2:
            raise ValueError(
                f"Expected 2-D array from {npy_path} (channel '{ch_name}'), got shape {arr.shape}."
            )
        if arr.shape[1] < 1:
            raise ValueError(f".npy file for channel '{ch_name}' has 0 feature columns: {npy_path}")

        primary = arr[:, 0].astype(np.float64)
        if not np.all(np.isfinite(primary)):
            raise ValueError(
                f"Primary signal (col 0) of channel '{ch_name}' ({npy_path}) "
                f"contains non-finite values (NaN or Inf)."
            )

        if n_steps is None:
            n_steps = arr.shape[0]
        elif arr.shape[0] != n_steps:
            raise ValueError(
                f"Timestep count mismatch: channel '{ch_name}' has "
                f"{arr.shape[0]} steps, expected {n_steps} to match "
                f"previously loaded channels. All channels in a multi-channel "
                f"window set must have identical timestep counts."
            )

        channel_signals[ch_name] = primary.tolist()

    assert n_steps is not None  # guaranteed by non-empty check above

    subsystem_enum = Subsystem(str(subsystem).lower())
    t0 = base_timestamp or datetime(2024, 1, 1, 0, 0, tzinfo=UTC)

    if n_steps < window_size:
        return

    intervals = label_intervals or []

    for start_idx in range(0, n_steps - window_size + 1, stride):
        end_idx = start_idx + window_size
        start_time = t0 + timedelta(seconds=start_idx * time_step_seconds)
        end_time = t0 + timedelta(seconds=(end_idx - 1) * time_step_seconds)

        window_channels = {ch: sig[start_idx:end_idx] for ch, sig in channel_signals.items()}

        is_anomalous = _window_overlaps_anomaly(start_idx, end_idx, intervals)

        yield TelemetryWindow(
            subsystem=subsystem_enum,
            start_time=start_time,
            end_time=end_time,
            channels=window_channels,
            source_dataset=source_name,
            metadata={
                "start_index": start_idx,
                "end_index": end_idx,
                "is_anomalous": is_anomalous,
                "channel_files": {ch: p.name for ch, p in channel_paths.items()},
            },
        )
