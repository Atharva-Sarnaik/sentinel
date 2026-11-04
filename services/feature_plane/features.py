"""
services.feature_plane.features
=================================
Feature extraction from normalised telemetry windows.

Outputs are stored in Parquet + DuckDB (feature store).

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import TelemetryWindow


def extract_features(window: TelemetryWindow) -> dict[str, float]:
    """
    Extract statistical and temporal features from a normalised window.

    Returns:
        dict mapping feature name to scalar value.

    Raises:
        NotImplementedError: Implementation pending task T0.9.
    """
    # TODO (T0.9): implement feature extraction.
    raise NotImplementedError("extract_features: implementation pending task T0.9.")
