"""
services.specialists.specialist
=================================
Specialist agent detector combining LSTMAETemplate and DynamicThresholder
to produce typed SpecialistOpinion contract instances.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.3, T1.4, T1.5)
Status:  complete — integrated specialist detector with save/load and inference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from libs.common.helpers import utc_now
from libs.contracts import Severity, SpecialistOpinion, Subsystem, TelemetryWindow
from services.specialists.lstm_ae_template import LSTMAETemplate
from services.specialists.thresholding import DynamicThresholder


class SpecialistDetector:
    """
    Trained specialist detector for a single spacecraft subsystem.

    Integrates LSTMAETemplate with DynamicThresholder to assess TelemetryWindows
    and produce validated SpecialistOpinion instances.
    """

    def __init__(
        self,
        subsystem: Subsystem,
        model: LSTMAETemplate,
        thresholder: DynamicThresholder,
        model_run_id: str = "specialist-local-run",
    ) -> None:
        self.subsystem = subsystem
        self.model = model
        self.thresholder = thresholder
        self.model_run_id = model_run_id

    def analyze(self, window: TelemetryWindow) -> SpecialistOpinion:
        """
        Evaluate a TelemetryWindow and produce a SpecialistOpinion.
        """
        error = self.model.reconstruction_error(window)
        ch_errors = self.model.channel_reconstruction_errors(window)

        score = self.thresholder.score(error)
        severity = self.thresholder.severity_for(error)
        thresh_val = self.thresholder.threshold_value

        # Identify responsible channels
        responsible = [ch for ch, err in ch_errors.items() if err >= thresh_val]
        if not responsible and score >= 0.5:
            sorted_chs = sorted(ch_errors.items(), key=lambda kv: kv[1], reverse=True)
            responsible = [sorted_chs[0][0]] if sorted_chs else []

        # If score is below 0.5, ensure severity is nominal
        if score < 0.5:
            severity = Severity.NOMINAL

        return SpecialistOpinion(
            window_id=window.window_id,
            subsystem=self.subsystem,
            anomaly_score=score,
            severity=severity,
            responsible_channels=responsible,
            threshold_used=thresh_val,
            model_run_id=self.model_run_id,
            created_at=utc_now(),
        )

    def save(self, path: Path | str) -> None:
        """Save model and thresholder checkpoint."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "subsystem": self.subsystem.value,
            "model_config": self.model.config,
            "model_run_id": self.model_run_id,
            "model_state_dict": self.model.model.state_dict(),
            "threshold_value": self.thresholder.threshold_value,
            "threshold_mean": self.thresholder._mean,
            "threshold_std": self.thresholder._std,
            "threshold_percentile": self.thresholder.default_percentile,
        }
        torch.save(checkpoint, dest)

    @classmethod
    def load(cls, path: Path | str) -> SpecialistDetector:
        """Load specialist detector from saved checkpoint."""
        dest = Path(path)
        checkpoint = torch.load(dest, map_location="cpu", weights_only=False)

        subsystem = Subsystem(checkpoint["subsystem"])
        model_config: dict[str, Any] = checkpoint["model_config"]
        model = LSTMAETemplate(model_config)
        model.model.load_state_dict(checkpoint["model_state_dict"])
        model.is_trained = True

        thresholder = DynamicThresholder(default_percentile=checkpoint["threshold_percentile"])
        thresholder._threshold = checkpoint["threshold_value"]
        thresholder._mean = checkpoint["threshold_mean"]
        thresholder._std = checkpoint["threshold_std"]
        thresholder.is_fitted = True

        return cls(
            subsystem=subsystem,
            model=model,
            thresholder=thresholder,
            model_run_id=checkpoint.get("model_run_id", "loaded-specialist"),
        )
