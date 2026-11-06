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

import math

from libs.contracts import TelemetryWindow


def extract_features(window: TelemetryWindow) -> dict[str, float]:
    """
    Extract statistical and temporal features from a normalised window.

    Features computed per channel:
      - mean
      - std
      - min
      - max
      - delta (last - first)

    Returns:
        dict mapping feature name to scalar float value.
    """
    features: dict[str, float] = {}

    for ch, series in window.channels.items():
        if not series:
            continue

        mean_val = sum(series) / len(series)
        var_val = sum((x - mean_val) ** 2 for x in series) / max(1, len(series) - 1)
        std_val = math.sqrt(var_val)

        features[f"{ch}__mean"] = mean_val
        features[f"{ch}__std"] = std_val
        features[f"{ch}__min"] = min(series)
        features[f"{ch}__max"] = max(series)
        features[f"{ch}__delta"] = series[-1] - series[0]

    return features
