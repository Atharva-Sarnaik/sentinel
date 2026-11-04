"""
services.baselines.combined_lstm_ae
======================================
Arm C: single combined LSTM Autoencoder trained on all subsystems.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.6)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import SpecialistOpinion, TelemetryWindow


def run_combined_lstm_ae(
    window: TelemetryWindow,
    model_path: str,
) -> SpecialistOpinion:
    """
    Classify a window using a combined (all-subsystem) LSTM-AE (arm C).

    Raises:
        NotImplementedError: Implementation pending task T1.6.
    """
    # TODO (T1.6): implement single combined LSTM-AE baseline.
    raise NotImplementedError("run_combined_lstm_ae: implementation pending task T1.6.")
