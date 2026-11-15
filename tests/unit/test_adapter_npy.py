"""
tests.unit.test_adapter_npy
============================
Unit tests for the NumPy telemetry adapter extensions (Task T0.7).

Covers:
  • Single-channel .npy streaming  (stream_npy_windows)
  • Multi-channel .npy merging     (stream_npy_multi_channel_windows)
  • Label parsing                  (load_smap_labels)
  • Shape / dimension validation
  • Timestamp alignment and chronological ordering
  • Anomaly label propagation (inclusive endpoints per Hundman KDD 2018)
  • Data leakage prevention

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.7)
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from libs.common.helpers import assert_no_future_leakage
from libs.contracts import Subsystem, TelemetryWindow
from services.data_plane.adapter import (
    load_smap_labels,
    stream_npy_multi_channel_windows,
    stream_npy_windows,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NPY_FEATURES = 25  # standard SMAP feature count


def _write_npy(path: Path, n_steps: int, n_features: int = NPY_FEATURES) -> np.ndarray:
    """Create a deterministic 2-D .npy file and return the array."""
    rng = np.random.default_rng(42)
    arr = rng.standard_normal((n_steps, n_features)).astype(np.float32)
    np.save(path, arr)
    return arr


def _write_labels_csv(path: Path, rows: list[dict]) -> None:
    """Write a minimal labeled_anomalies.csv."""
    fieldnames = ["chan_id", "spacecraft", "anomaly_sequences", "class", "num_values"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# =========================================================================
# Single-channel .npy tests
# =========================================================================


class TestStreamNpyWindows:
    """Tests for stream_npy_windows()."""

    def test_basic_streaming(self, tmp_path: Path) -> None:
        """Valid .npy file produces correct number of windows with correct channels."""
        npy_path = tmp_path / "P-1.npy"
        _write_npy(npy_path, n_steps=200)

        windows = list(
            stream_npy_windows(
                npy_path,
                "P-1",
                Subsystem.POWER,
                window_size=50,
                stride=10,
            )
        )

        expected_count = (200 - 50) // 10 + 1  # = 16
        assert len(windows) == expected_count
        for w in windows:
            assert isinstance(w, TelemetryWindow)
            assert "P-1" in w.channels
            assert w.window_length == 50
            assert w.subsystem == Subsystem.POWER
            assert w.source_dataset == "SMAP"

    def test_chronological_order(self, tmp_path: Path) -> None:
        """Windows must be strictly increasing in start_time."""
        npy_path = tmp_path / "T-1.npy"
        _write_npy(npy_path, n_steps=300)

        windows = list(stream_npy_windows(npy_path, "T-1", "thermal", window_size=50, stride=20))
        assert len(windows) > 1
        for i in range(len(windows) - 1):
            assert windows[i].start_time < windows[i + 1].start_time
            assert windows[i].end_time < windows[i + 1].end_time

    def test_channel_values_from_column_zero(self, tmp_path: Path) -> None:
        """Channel values must come from column 0 of the .npy array."""
        npy_path = tmp_path / "P-1.npy"
        arr = _write_npy(npy_path, n_steps=200)

        windows = list(stream_npy_windows(npy_path, "P-1", "power", window_size=50, stride=50))
        first = windows[0]
        expected = arr[:50, 0].astype(np.float64).tolist()
        actual = first.channels["P-1"]
        np.testing.assert_allclose(actual, expected, rtol=1e-5)

    def test_invalid_shape_1d(self, tmp_path: Path) -> None:
        """1-D .npy array must raise ValueError."""
        npy_path = tmp_path / "bad.npy"
        np.save(npy_path, np.zeros(100))

        with pytest.raises(ValueError, match="2-D"):
            list(stream_npy_windows(npy_path, "P-1", "power"))

    def test_invalid_shape_3d(self, tmp_path: Path) -> None:
        """3-D .npy array must raise ValueError."""
        npy_path = tmp_path / "bad.npy"
        np.save(npy_path, np.zeros((10, 5, 3)))

        with pytest.raises(ValueError, match="2-D"):
            list(stream_npy_windows(npy_path, "P-1", "power"))

    def test_zero_columns(self, tmp_path: Path) -> None:
        """Array with 0 feature columns must raise ValueError."""
        npy_path = tmp_path / "bad.npy"
        np.save(npy_path, np.zeros((200, 0)))

        with pytest.raises(ValueError, match="0 feature columns"):
            list(stream_npy_windows(npy_path, "P-1", "power"))

    def test_too_short_for_window(self, tmp_path: Path) -> None:
        """Array shorter than window_size must yield 0 windows."""
        npy_path = tmp_path / "short.npy"
        _write_npy(npy_path, n_steps=30)

        windows = list(stream_npy_windows(npy_path, "P-1", "power", window_size=50))
        assert len(windows) == 0

    def test_label_propagation_inclusive_endpoints(self, tmp_path: Path) -> None:
        """Windows overlapping inclusive anomaly intervals must be marked anomalous.

        Hundman et al. (KDD 2018) convention: [start, end] both inclusive.
        """
        npy_path = tmp_path / "P-1.npy"
        _write_npy(npy_path, n_steps=200)

        # Anomaly at indices [50, 99] inclusive → steps 50..99
        labels = [(50, 99)]

        windows = list(
            stream_npy_windows(
                npy_path,
                "P-1",
                "power",
                window_size=50,
                stride=50,
                label_intervals=labels,
            )
        )
        # Windows: [0,50), [50,100), [100,150), [150,200)
        assert len(windows) == 4
        assert windows[0].metadata["is_anomalous"] is False  # [0, 50)   – no overlap
        assert windows[1].metadata["is_anomalous"] is True  # [50, 100) – full overlap
        assert windows[2].metadata["is_anomalous"] is False  # [100, 150)
        assert windows[3].metadata["is_anomalous"] is False  # [150, 200)

    def test_label_partial_overlap(self, tmp_path: Path) -> None:
        """A window partially overlapping an anomaly interval must be marked anomalous."""
        npy_path = tmp_path / "P-1.npy"
        _write_npy(npy_path, n_steps=200)

        # Anomaly at [40, 60] inclusive – overlaps both [0,50) and [50,100)
        labels = [(40, 60)]
        windows = list(
            stream_npy_windows(
                npy_path,
                "P-1",
                "power",
                window_size=50,
                stride=50,
                label_intervals=labels,
            )
        )
        assert windows[0].metadata["is_anomalous"] is True  # [0, 50)  – overlap at 40-49
        assert windows[1].metadata["is_anomalous"] is True  # [50, 100) – overlap at 50-60

    def test_no_label_leakage_train_has_no_labels(self, tmp_path: Path) -> None:
        """Train windows (no label_intervals) must never have is_anomalous=True."""
        npy_path = tmp_path / "P-1.npy"
        _write_npy(npy_path, n_steps=200)

        # Train: no labels
        train_wins = list(stream_npy_windows(npy_path, "P-1", "power", window_size=50, stride=50))
        for w in train_wins:
            assert w.metadata["is_anomalous"] is False

    def test_timestamp_alignment(self, tmp_path: Path) -> None:
        """First window start_time must equal base_timestamp; timestamps are contiguous."""
        npy_path = tmp_path / "P-1.npy"
        _write_npy(npy_path, n_steps=200)

        base = datetime(2025, 6, 1, 0, 0, tzinfo=UTC)
        windows = list(
            stream_npy_windows(
                npy_path,
                "P-1",
                "power",
                window_size=50,
                stride=50,
                base_timestamp=base,
            )
        )
        assert windows[0].start_time == base
        # Second window starts at base + 50 seconds
        assert windows[1].start_time == base + timedelta(seconds=50)

    def test_train_test_no_leakage(self, tmp_path: Path) -> None:
        """Synthetic train/test .npy files with offset timestamps must pass leakage check."""
        train_path = tmp_path / "train_P-1.npy"
        test_path = tmp_path / "test_P-1.npy"
        _write_npy(train_path, n_steps=200)
        _write_npy(test_path, n_steps=100)

        base = datetime(2024, 1, 1, tzinfo=UTC)
        train_wins = list(
            stream_npy_windows(
                train_path,
                "P-1",
                "power",
                window_size=50,
                stride=50,
                base_timestamp=base,
            )
        )
        # Test base: offset by n_train_steps * Δt
        test_base = base + timedelta(seconds=200)
        test_wins = list(
            stream_npy_windows(
                test_path,
                "P-1",
                "power",
                window_size=50,
                stride=50,
                base_timestamp=test_base,
            )
        )

        train_end_times = [w.end_time for w in train_wins]
        test_start_times = [w.start_time for w in test_wins]

        # Must not raise
        assert_no_future_leakage(train_end_times, test_start_times)

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError for non-existent .npy path."""
        with pytest.raises(FileNotFoundError):
            list(stream_npy_windows(tmp_path / "ghost.npy", "P-1", "power"))

    def test_nonfinite_values_rejected(self, tmp_path: Path) -> None:
        """NaN / Inf in column 0 must raise ValueError."""
        npy_path = tmp_path / "bad.npy"
        arr = np.ones((100, 5), dtype=np.float32)
        arr[50, 0] = np.nan
        np.save(npy_path, arr)

        with pytest.raises(ValueError, match="non-finite"):
            list(stream_npy_windows(npy_path, "P-1", "power", window_size=10))


# =========================================================================
# Label loader tests
# =========================================================================


class TestLoadSmapLabels:
    """Tests for load_smap_labels()."""

    def test_basic_parsing(self, tmp_path: Path) -> None:
        """Correctly parse anomaly_sequences for a known channel."""
        csv_path = tmp_path / "labeled_anomalies.csv"
        _write_labels_csv(
            csv_path,
            [
                {
                    "chan_id": "P-1",
                    "spacecraft": "SMAP",
                    "anomaly_sequences": "[[4690, 4774], [8100, 8200]]",
                    "class": "contextual",
                    "num_values": "8505",
                },
                {
                    "chan_id": "T-1",
                    "spacecraft": "SMAP",
                    "anomaly_sequences": "[[100, 200]]",
                    "class": "point",
                    "num_values": "3000",
                },
            ],
        )

        intervals = load_smap_labels(csv_path, "P-1")
        assert intervals == [(4690, 4774), (8100, 8200)]

    def test_missing_channel_returns_empty(self, tmp_path: Path) -> None:
        """Unknown chan_id returns an empty list."""
        csv_path = tmp_path / "labeled_anomalies.csv"
        _write_labels_csv(
            csv_path,
            [
                {
                    "chan_id": "P-1",
                    "spacecraft": "SMAP",
                    "anomaly_sequences": "[[10, 20]]",
                    "class": "point",
                    "num_values": "100",
                },
            ],
        )

        intervals = load_smap_labels(csv_path, "NONEXISTENT")
        assert intervals == []

    def test_spacecraft_filter(self, tmp_path: Path) -> None:
        """Only rows matching the specified spacecraft are returned."""
        csv_path = tmp_path / "labeled_anomalies.csv"
        _write_labels_csv(
            csv_path,
            [
                {
                    "chan_id": "P-1",
                    "spacecraft": "SMAP",
                    "anomaly_sequences": "[[10, 20]]",
                    "class": "point",
                    "num_values": "100",
                },
                {
                    "chan_id": "P-1",
                    "spacecraft": "MSL",
                    "anomaly_sequences": "[[30, 40]]",
                    "class": "point",
                    "num_values": "100",
                },
            ],
        )

        smap_intervals = load_smap_labels(csv_path, "P-1", spacecraft="SMAP")
        assert smap_intervals == [(10, 20)]

        msl_intervals = load_smap_labels(csv_path, "P-1", spacecraft="MSL")
        assert msl_intervals == [(30, 40)]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError for non-existent CSV."""
        with pytest.raises(FileNotFoundError):
            load_smap_labels(tmp_path / "nope.csv", "P-1")


# =========================================================================
# Multi-channel .npy tests
# =========================================================================


class TestStreamNpyMultiChannelWindows:
    """Tests for stream_npy_multi_channel_windows()."""

    def test_basic_multi_channel(self, tmp_path: Path) -> None:
        """Merging 4 channels produces windows with all 4 keys."""
        channel_paths: dict[str, Path] = {}
        for ch in ["P-1", "P-2", "P-3", "P-4"]:
            p = tmp_path / f"{ch}.npy"
            _write_npy(p, n_steps=200)
            channel_paths[ch] = p

        windows = list(
            stream_npy_multi_channel_windows(
                channel_paths,
                "power",
                window_size=50,
                stride=50,
            )
        )

        assert len(windows) == 4  # (200 - 50) // 50 + 1
        for w in windows:
            assert sorted(w.channels.keys()) == ["P-1", "P-2", "P-3", "P-4"]
            assert w.window_length == 50
            assert w.subsystem == Subsystem.POWER

    def test_channel_values_correct(self, tmp_path: Path) -> None:
        """Each channel's values must come from column 0 of its own .npy file."""
        arrs: dict[str, np.ndarray] = {}
        paths: dict[str, Path] = {}
        for ch in ["T-1", "T-2", "T-3"]:
            p = tmp_path / f"{ch}.npy"
            a = _write_npy(p, n_steps=100)
            arrs[ch] = a
            paths[ch] = p

        windows = list(
            stream_npy_multi_channel_windows(
                paths,
                "thermal",
                window_size=100,
                stride=100,
            )
        )
        assert len(windows) == 1
        w = windows[0]
        for ch in ["T-1", "T-2", "T-3"]:
            expected = arrs[ch][:100, 0].astype(np.float64).tolist()
            np.testing.assert_allclose(w.channels[ch], expected, rtol=1e-5)

    def test_chronological_order(self, tmp_path: Path) -> None:
        """Multi-channel windows must be strictly chronologically ordered."""
        paths: dict[str, Path] = {}
        for ch in ["A-1", "A-2"]:
            p = tmp_path / f"{ch}.npy"
            _write_npy(p, n_steps=300)
            paths[ch] = p

        windows = list(
            stream_npy_multi_channel_windows(
                paths,
                "attitude",
                window_size=50,
                stride=20,
            )
        )
        assert len(windows) > 1
        for i in range(len(windows) - 1):
            assert windows[i].start_time < windows[i + 1].start_time

    def test_timestep_count_mismatch_rejected(self, tmp_path: Path) -> None:
        """Channels with different timestep counts must raise ValueError."""
        p1 = tmp_path / "P-1.npy"
        p2 = tmp_path / "P-2.npy"
        _write_npy(p1, n_steps=200)
        _write_npy(p2, n_steps=150)  # different length

        with pytest.raises(ValueError, match="Timestep count mismatch"):
            list(
                stream_npy_multi_channel_windows(
                    {"P-1": p1, "P-2": p2},
                    "power",
                    window_size=50,
                )
            )

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        """FileNotFoundError if any channel .npy is missing."""
        p1 = tmp_path / "P-1.npy"
        _write_npy(p1, n_steps=200)

        with pytest.raises(FileNotFoundError, match="P-2"):
            list(
                stream_npy_multi_channel_windows(
                    {"P-1": p1, "P-2": tmp_path / "P-2.npy"},
                    "power",
                    window_size=50,
                )
            )

    def test_empty_channel_paths_rejected(self) -> None:
        """Empty channel_paths dict must raise ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            list(stream_npy_multi_channel_windows({}, "power"))

    def test_label_propagation_multi_channel(self, tmp_path: Path) -> None:
        """Label intervals propagate correctly to multi-channel windows."""
        paths: dict[str, Path] = {}
        for ch in ["C-1", "C-2", "D-1"]:
            p = tmp_path / f"{ch}.npy"
            _write_npy(p, n_steps=200)
            paths[ch] = p

        labels = [(60, 80)]  # inclusive endpoints
        windows = list(
            stream_npy_multi_channel_windows(
                paths,
                "communications",
                window_size=50,
                stride=50,
                label_intervals=labels,
            )
        )
        # Windows: [0,50), [50,100), [100,150), [150,200)
        assert windows[0].metadata["is_anomalous"] is False  # [0, 50)
        assert windows[1].metadata["is_anomalous"] is True  # [50, 100) overlaps [60,80]
        assert windows[2].metadata["is_anomalous"] is False
        assert windows[3].metadata["is_anomalous"] is False

    def test_deterministic_channel_ordering(self, tmp_path: Path) -> None:
        """Channel keys in each window must be in sorted order regardless of input order."""
        paths: dict[str, Path] = {}
        # Insert in reverse order
        for ch in ["P-4", "P-3", "P-2", "P-1"]:
            p = tmp_path / f"{ch}.npy"
            _write_npy(p, n_steps=100)
            paths[ch] = p

        windows = list(
            stream_npy_multi_channel_windows(
                paths,
                "power",
                window_size=50,
                stride=50,
            )
        )
        for w in windows:
            assert list(w.channels.keys()) == ["P-1", "P-2", "P-3", "P-4"]

    def test_nonfinite_in_one_channel_rejected(self, tmp_path: Path) -> None:
        """NaN in any channel's column 0 must raise ValueError."""
        p1 = tmp_path / "P-1.npy"
        _write_npy(p1, n_steps=100)

        p2 = tmp_path / "P-2.npy"
        bad = np.ones((100, 25), dtype=np.float32)
        bad[50, 0] = np.inf
        np.save(p2, bad)

        with pytest.raises(ValueError, match="non-finite"):
            list(
                stream_npy_multi_channel_windows(
                    {"P-1": p1, "P-2": p2},
                    "power",
                    window_size=50,
                )
            )
