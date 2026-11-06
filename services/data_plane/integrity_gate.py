"""
services.data_plane.integrity_gate
====================================
Schema validation, range checks, and staleness detection for incoming windows.

Inputs:  raw TelemetryWindow from the adapter
Outputs: validated TelemetryWindow or raises DataIntegrityError

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.8)
Status:  complete — schema, range, NaN/Inf, and staleness validation.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from libs.contracts import TelemetryWindow


class DataIntegrityError(Exception):
    """Raised when a TelemetryWindow fails data integrity validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


# Default physical bounds for common satellite telemetry channels
DEFAULT_CHANNEL_BOUNDS: dict[str, tuple[float, float]] = {
    # Power (Volts / Amps / Percent)
    "P-1": (-10.0, 100.0),  # Bus Voltage (V)
    "P-2": (-50.0, 100.0),  # Solar Array Current (A)
    "P-3": (0.0, 100.0),  # Battery SOC (%)
    "P-4": (0.0, 50.0),  # Cell Voltage (V)
    # Thermal (deg C / Kelvin)
    "T-1": (-150.0, 200.0),  # Panel Temp (C)
    "T-2": (-100.0, 150.0),  # Box Temp (C)
    "T-3": (-50.0, 100.0),  # Battery Temp (C)
    # Attitude (Quaternion / Angular rate)
    "A-1": (-10000.0, 10000.0),  # Wheel Speed (RPM)
    "A-2": (-10000.0, 10000.0),
    "A-3": (-50.0, 50.0),  # Gyro rate (deg/s)
    "A-4": (-1.1, 1.1),  # Quaternion component
    # Communications
    "C-1": (-200.0, 50.0),  # RSSI (dBm)
    "C-2": (0.0, 100.0),  # Tx Power (W)
    "D-1": (0.0, 100.0),  # Buffer fill level (%)
}


def validate_window(
    window: TelemetryWindow,
    channel_bounds: dict[str, tuple[float, float]] | None = None,
    max_staleness_seconds: float | None = None,
    reference_time: datetime | None = None,
) -> TelemetryWindow:
    """
    Validate a TelemetryWindow for schema correctness, value ranges,
    NaN/Inf corruptions, and staleness.

    Args:
        window: The TelemetryWindow to validate.
        channel_bounds: Optional dict mapping channel name to (min_val, max_val).
        max_staleness_seconds: Maximum allowed age of end_time relative to reference_time.
        reference_time: Reference datetime for staleness checks (defaults to UTC now).

    Returns:
        The validated TelemetryWindow if all checks pass.

    Raises:
        DataIntegrityError: If the window is empty, contains NaN/Inf values,
                            violates physical range limits, or is stale.
    """
    # 1. Structural / Emptiness Check
    if not window.channels:
        raise DataIntegrityError(
            "Window rejected: channel dictionary is empty.",
            details={"window_id": str(window.window_id), "subsystem": str(window.subsystem)},
        )

    if window.window_length == 0:
        raise DataIntegrityError(
            "Window rejected: channel series contains 0 timesteps.",
            details={"window_id": str(window.window_id)},
        )

    # 2. Staleness Check
    if max_staleness_seconds is not None:
        now = reference_time or datetime.now(UTC)
        # Ensure window.end_time has timezone info for comparison
        end_t = window.end_time if window.end_time.tzinfo else window.end_time.replace(tzinfo=UTC)
        age_seconds = (now - end_t).total_seconds()
        if age_seconds > max_staleness_seconds:
            raise DataIntegrityError(
                f"Window rejected for staleness: age {age_seconds:.1f}s exceeds limit {max_staleness_seconds:.1f}s",
                details={
                    "window_id": str(window.window_id),
                    "age_seconds": age_seconds,
                    "max_allowed": max_staleness_seconds,
                },
            )

    # 3. Numeric Integrity & Range Checks
    bounds_map = channel_bounds or DEFAULT_CHANNEL_BOUNDS

    for channel_name, series in window.channels.items():
        bounds = bounds_map.get(channel_name)

        for step_idx, val in enumerate(series):
            # Check NaN or Inf
            if math.isnan(val) or math.isinf(val):
                raise DataIntegrityError(
                    f"Corrupt sensor data in channel '{channel_name}' at step {step_idx}: non-finite value ({val})",
                    details={
                        "window_id": str(window.window_id),
                        "channel": channel_name,
                        "step_index": step_idx,
                        "value": str(val),
                    },
                )

            # Check bounds if defined
            if bounds is not None:
                min_val, max_val = bounds
                if not (min_val <= val <= max_val):
                    raise DataIntegrityError(
                        f"Range violation in channel '{channel_name}' at step {step_idx}: value {val} outside [{min_val}, {max_val}]",
                        details={
                            "window_id": str(window.window_id),
                            "channel": channel_name,
                            "step_index": step_idx,
                            "value": val,
                            "bounds": bounds,
                        },
                    )

    return window
