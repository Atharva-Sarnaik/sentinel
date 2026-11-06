"""
services.feature_plane.features
=================================
Feature extraction from normalised telemetry windows.

Outputs are stored in Parquet + DuckDB (feature store).

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  complete — statistical features (mean, std, min, max, delta).
"""

from __future__ import annotations

from libs.common.helpers import extract_window_features
from libs.contracts import TelemetryWindow


def extract_features(window: TelemetryWindow) -> dict[str, float]:
    """
    Extract statistical and temporal features from a normalised window.

    Returns:
        dict mapping feature name to scalar float value.
    """
    return extract_window_features(window.channels)
