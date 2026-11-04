"""
services.feature_plane.normalisation
======================================
Per-channel normalisation (fit on train set only).

Design rule (ADR-0002): normalisation statistics are computed on the
training partition only. Applying train-set statistics to the test set
is mandatory; fitting on the full dataset constitutes leakage.

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import TelemetryWindow


class ChannelNormaliser:
    """Fit z-score normaliser on training windows; transform any window."""

    def fit(self, windows: list[TelemetryWindow]) -> None:
        """Fit mean/std from training windows only."""
        # TODO (T0.9): implement fit.
        raise NotImplementedError("ChannelNormaliser.fit: pending task T0.9.")

    def transform(self, window: TelemetryWindow) -> TelemetryWindow:
        """Apply fitted normalisation to a single window."""
        # TODO (T0.9): implement transform.
        raise NotImplementedError("ChannelNormaliser.transform: pending task T0.9.")
