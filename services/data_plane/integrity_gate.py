"""
services.data_plane.integrity_gate
====================================
Schema validation, range checks, and staleness detection for incoming windows.

Inputs:  raw TelemetryWindow from the adapter
Outputs: validated TelemetryWindow or raises DataIntegrityError

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.8)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import TelemetryWindow


class DataIntegrityError(Exception):
    """Raised when a TelemetryWindow fails validation."""


def validate_window(window: TelemetryWindow) -> TelemetryWindow:
    """
    Validate a TelemetryWindow for schema correctness, value ranges,
    and staleness.

    Args:
        window: The window to validate.

    Returns:
        The same window if valid.

    Raises:
        DataIntegrityError: If the window is stale, malformed, or
                            contains out-of-range channel values.
        NotImplementedError: Implementation pending task T0.8.
    """
    # TODO (T0.8): implement schema, range, and staleness checks.
    raise NotImplementedError("validate_window: implementation pending task T0.8.")
