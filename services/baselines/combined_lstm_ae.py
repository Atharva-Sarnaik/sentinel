"""
services.baselines.combined_lstm_ae
======================================
Arm C: single combined LSTM Autoencoder trained on all subsystems simultaneously.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.6)
Status:  complete — single combined PyTorch LSTM-AE taking all channels with thresholding and channel attribution.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from libs.common.helpers import utc_now
from libs.contracts import Severity, SpecialistOpinion, Subsystem, TelemetryWindow


class _CombinedEncoderDecoder(nn.Module):
    """PyTorch Sequence-to-Sequence Autoencoder for multi-subsystem telemetry."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_layers: int = 2,
        latent_dim: int = 64,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.latent_dim = latent_dim

        # Encoder
        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc_latent = nn.Linear(hidden_dim, latent_dim)

        # Decoder
        self.fc_decode = nn.Linear(latent_dim, hidden_dim)
        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.output_layer = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        _, (h_n, _) = self.encoder(x)
        latent = self.fc_latent(h_n[-1])

        decoder_input = self.fc_decode(latent).unsqueeze(1).repeat(1, seq_len, 1)
        dec_out, _ = self.decoder(decoder_input)
        return self.output_layer(dec_out)


class CombinedLSTMAEDetector:
    """
    Arm C Baseline: A single monolithic LSTM Autoencoder trained on all telemetry channels.
    """

    def __init__(
        self,
        channels: list[str],
        hidden_dim: int = 128,
        num_layers: int = 2,
        latent_dim: int = 64,
        model_run_id: str = "baseline-arm-c-combined-lstm-ae",
    ) -> None:
        if not channels:
            raise ValueError("channels list must not be empty.")

        self.channels = sorted(channels)
        self.input_dim = len(self.channels)
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.latent_dim = latent_dim
        self.model_run_id = model_run_id

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _CombinedEncoderDecoder(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            latent_dim=self.latent_dim,
        ).to(self.device)

        self.is_trained: bool = False
        self.threshold: float = 0.0

    def _window_to_array(self, window: TelemetryWindow) -> np.ndarray:
        """Convert window to (seq_len, input_dim) array in sorted channel order."""
        seq_len = window.window_length
        matrix = np.zeros((seq_len, self.input_dim), dtype=np.float32)

        for col_idx, ch in enumerate(self.channels):
            series = window.channels.get(ch)
            if series is not None:
                matrix[:, col_idx] = series
            else:
                matrix[:, col_idx] = 0.0

        return matrix

    def train(
        self,
        windows: list[TelemetryWindow],
        epochs: int = 20,
        batch_size: int = 32,
        lr: float = 1e-3,
        percentile: float = 95.0,
    ) -> dict[str, Any]:
        """Train the combined LSTM-AE model and fit its dynamic threshold."""
        if not windows:
            raise ValueError("Cannot train on empty windows list.")

        arrays = [self._window_to_array(w) for w in windows]
        x_train = np.stack(arrays, axis=0)  # (N, seq_len, input_dim)

        tensor_x = torch.from_numpy(x_train).float()
        dataset = TensorDataset(tensor_x, tensor_x)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        loss_history: list[float] = []

        for _epoch in range(epochs):
            total_loss = 0.0
            for batch_x, batch_target in loader:
                batch_x = batch_x.to(self.device)
                batch_target = batch_target.to(self.device)

                optimizer.zero_grad()
                reconstructed = self.model(batch_x)
                loss = criterion(reconstructed, batch_target)
                loss.backward()
                optimizer.step()

                total_loss += loss.item() * len(batch_x)

            epoch_loss = total_loss / len(windows)
            loss_history.append(epoch_loss)

        self.is_trained = True

        # Fit threshold from training errors
        errors = [self.reconstruction_error(w) for w in windows]
        sorted_errors = sorted(errors)
        rank_idx = int(math.ceil((percentile / 100.0) * len(sorted_errors))) - 1
        rank_idx = max(0, min(rank_idx, len(sorted_errors) - 1))
        self.threshold = max(sorted_errors[rank_idx], 1e-4)

        return {
            "loss_history": loss_history,
            "final_loss": loss_history[-1] if loss_history else 0.0,
            "threshold": self.threshold,
            "samples_trained": len(windows),
        }

    def reconstruction_error(self, window: TelemetryWindow) -> float:
        """Compute Mean Squared Error (MSE) reconstruction error."""
        if not self.is_trained:
            raise RuntimeError("CombinedLSTMAEDetector must be trained before inference.")

        self.model.eval()
        arr = self._window_to_array(window)
        tensor_in = torch.from_numpy(arr).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            reconstructed = self.model(tensor_in).squeeze(0).cpu().numpy()

        mse = float(np.mean((arr - reconstructed) ** 2))
        return mse

    def channel_reconstruction_errors(self, window: TelemetryWindow) -> dict[str, float]:
        """Compute per-channel MSE reconstruction errors."""
        if not self.is_trained:
            raise RuntimeError("CombinedLSTMAEDetector must be trained before inference.")

        self.model.eval()
        arr = self._window_to_array(window)
        tensor_in = torch.from_numpy(arr).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            reconstructed = self.model(tensor_in).squeeze(0).cpu().numpy()

        channel_mse = np.mean((arr - reconstructed) ** 2, axis=0)
        return {ch: float(channel_mse[i]) for i, ch in enumerate(self.channels)}

    def score(self, window: TelemetryWindow) -> float:
        """Convert reconstruction error into normalized anomaly score in [0.0, 1.0]."""
        error = self.reconstruction_error(window)
        thresh = max(self.threshold, 1e-6)

        if error < thresh:
            return (error / thresh) * 0.49
        excess = (error - thresh) / thresh
        return min(1.0, 0.5 + 0.5 * (1.0 - math.exp(-excess)))

    def predict(
        self,
        window: TelemetryWindow,
        subsystem: Subsystem = Subsystem.POWER,
    ) -> SpecialistOpinion:
        """Evaluate a window and produce a SpecialistOpinion."""
        ch_errors = self.channel_reconstruction_errors(window)
        score_val = self.score(window)

        # Attribute responsible channels whose error exceeds channel threshold
        thresh = max(self.threshold, 1e-6)
        responsible = [ch for ch, e in ch_errors.items() if e >= thresh]
        if not responsible and score_val >= 0.5:
            sorted_chs = sorted(ch_errors.items(), key=lambda kv: kv[1], reverse=True)
            responsible = [sorted_chs[0][0]] if sorted_chs else []

        if score_val < 0.5:
            severity = Severity.NOMINAL
        elif score_val < 0.8:
            severity = Severity.WARNING
        else:
            severity = Severity.CRITICAL

        return SpecialistOpinion(
            window_id=window.window_id,
            subsystem=subsystem,
            anomaly_score=score_val,
            severity=severity,
            responsible_channels=responsible,
            threshold_used=self.threshold,
            model_run_id=self.model_run_id,
            created_at=utc_now(),
        )

    def save(self, path: Path | str) -> None:
        """Save model weights and metadata checkpoint."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "channels": self.channels,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "latent_dim": self.latent_dim,
            "model_run_id": self.model_run_id,
            "is_trained": self.is_trained,
            "threshold": self.threshold,
            "state_dict": self.model.state_dict(),
        }
        torch.save(checkpoint, dest)

    @classmethod
    def load(cls, path: Path | str) -> CombinedLSTMAEDetector:
        """Load model weights and metadata from checkpoint."""
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
        detector = cls(
            channels=checkpoint["channels"],
            hidden_dim=checkpoint["hidden_dim"],
            num_layers=checkpoint["num_layers"],
            latent_dim=checkpoint["latent_dim"],
            model_run_id=checkpoint.get("model_run_id", "loaded-combined-lstm-ae"),
        )
        detector.model.load_state_dict(checkpoint["state_dict"])
        detector.is_trained = checkpoint.get("is_trained", True)
        detector.threshold = checkpoint.get("threshold", 0.0)
        return detector


def run_combined_lstm_ae(
    window: TelemetryWindow,
    model_path: str,
    subsystem: Subsystem = Subsystem.POWER,
) -> SpecialistOpinion:
    """
    Classify a window using a combined (all-subsystem) LSTM-AE checkpoint (arm C).
    """
    detector = CombinedLSTMAEDetector.load(model_path)
    return detector.predict(window, subsystem=subsystem)
