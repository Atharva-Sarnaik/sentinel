"""
services.feature_plane.normalisation
======================================
Per-channel normalisation (fit on train set only).

Design rule (ADR-0002): normalisation statistics are computed on the
training partition only. Applying train-set statistics to the test set
is mandatory; fitting on the full dataset constitutes leakage.

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  complete — z-score normalisation fit on training partition only.
"""

from __future__ import annotations

import math

from libs.contracts import TelemetryWindow


class ChannelNormaliser:
    """Fit z-score normaliser on training windows; transform any window."""

    def __init__(self) -> None:
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self.is_fitted: bool = False

    def fit(self, windows: list[TelemetryWindow]) -> ChannelNormaliser:
        """
        Fit mean and standard deviation from training windows only.

        Args:
            windows: Training set TelemetryWindows.

        Returns:
            self
        """
        if not windows:
            return self

        # Accumulate sums and squared sums per channel
        channel_vals: dict[str, list[float]] = {}
        for w in windows:
            for ch, series in w.channels.items():
                if ch not in channel_vals:
                    channel_vals[ch] = []
                channel_vals[ch].extend(series)

        for ch, values in channel_vals.items():
            if not values:
                continue
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / max(1, len(values) - 1)
            std_val = math.sqrt(variance)
            # Avoid division by zero for constant sensor signals
            self.means[ch] = mean_val
            self.stds[ch] = std_val if std_val > 1e-8 else 1.0

        self.is_fitted = True
        return self

    def transform(self, window: TelemetryWindow) -> TelemetryWindow:
        """
        Apply fitted normalisation to a single window.

        Args:
            window: TelemetryWindow to normalize.

        Returns:
            A new TelemetryWindow with normalized channel values.
        """
        if not self.is_fitted:
            raise RuntimeError("ChannelNormaliser must be fit on training data before transform.")

        norm_channels: dict[str, list[float]] = {}
        for ch, series in window.channels.items():
            mean = self.means.get(ch, 0.0)
            std = self.stds.get(ch, 1.0)
            norm_channels[ch] = [(x - mean) / std for x in series]

        return TelemetryWindow(
            window_id=window.window_id,
            subsystem=window.subsystem,
            start_time=window.start_time,
            end_time=window.end_time,
            channels=norm_channels,
            source_dataset=window.source_dataset,
            metadata={**window.metadata, "normalized": True},
        )
