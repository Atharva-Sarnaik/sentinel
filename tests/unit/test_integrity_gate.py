"""
tests.unit.test_integrity_gate
==============================
Unit tests for services.data_plane.integrity_gate (Task T0.8).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.8)
Status:  complete — validates schema, range, NaN/Inf, and staleness rejection.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from libs.contracts import Subsystem, TelemetryWindow
from services.data_plane.integrity_gate import DataIntegrityError, validate_window


@pytest.fixture
def valid_power_window() -> TelemetryWindow:
    t0 = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(seconds=99),
        channels={
            "P-1": [28.0] * 100,  # 28V bus voltage
            "P-2": [5.5] * 100,  # 5.5A current
        },
        source_dataset="SMAP",
    )


def test_valid_window_passes(valid_power_window: TelemetryWindow) -> None:
    """Test that a healthy, in-bounds window is returned untouched."""
    validated = validate_window(valid_power_window)
    assert validated.window_id == valid_power_window.window_id


def test_empty_channels_raises() -> None:
    """Test that window with no channels is rejected."""
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(seconds=10),
        channels={},
        source_dataset="SMAP",
    )
    with pytest.raises(DataIntegrityError, match="channel dictionary is empty"):
        validate_window(window)


def test_nan_value_rejected(valid_power_window: TelemetryWindow) -> None:
    """Test that NaN in any channel raises DataIntegrityError with details."""
    corrupt_channels = dict(valid_power_window.channels)
    corrupt_channels["P-1"] = [28.0] * 99 + [float("nan")]

    corrupt_window = TelemetryWindow(
        subsystem=valid_power_window.subsystem,
        start_time=valid_power_window.start_time,
        end_time=valid_power_window.end_time,
        channels=corrupt_channels,
        source_dataset=valid_power_window.source_dataset,
    )
    with pytest.raises(DataIntegrityError, match="non-finite value"):
        validate_window(corrupt_window)


def test_infinite_value_rejected(valid_power_window: TelemetryWindow) -> None:
    """Test that Inf in any channel raises DataIntegrityError."""
    corrupt_channels = dict(valid_power_window.channels)
    corrupt_channels["P-2"] = [math.inf] + [5.0] * 99

    corrupt_window = TelemetryWindow(
        subsystem=valid_power_window.subsystem,
        start_time=valid_power_window.start_time,
        end_time=valid_power_window.end_time,
        channels=corrupt_channels,
        source_dataset=valid_power_window.source_dataset,
    )
    with pytest.raises(DataIntegrityError, match="non-finite value"):
        validate_window(corrupt_window)


def test_range_violation_rejected(valid_power_window: TelemetryWindow) -> None:
    """Test that out-of-physical-range sensor values are rejected."""
    out_of_bounds_channels = dict(valid_power_window.channels)
    out_of_bounds_channels["P-1"] = [28.0] * 50 + [1500.0] + [28.0] * 49  # 1500V exceeds max (100V)

    window = TelemetryWindow(
        subsystem=valid_power_window.subsystem,
        start_time=valid_power_window.start_time,
        end_time=valid_power_window.end_time,
        channels=out_of_bounds_channels,
        source_dataset=valid_power_window.source_dataset,
    )
    with pytest.raises(DataIntegrityError, match="Range violation"):
        validate_window(window)


def test_staleness_rejection(valid_power_window: TelemetryWindow) -> None:
    """Test that a window exceeding max staleness threshold is rejected."""
    ref_time = valid_power_window.end_time + timedelta(seconds=300)  # 300 seconds later
    with pytest.raises(DataIntegrityError, match="Window rejected for staleness"):
        validate_window(valid_power_window, max_staleness_seconds=60.0, reference_time=ref_time)
