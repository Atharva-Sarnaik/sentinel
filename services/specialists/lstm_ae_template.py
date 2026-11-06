"""
services.specialists.lstm_ae_template
=======================================
Shared PyTorch LSTM Autoencoder template, parameterised per subsystem.

Each specialist (Power, Thermal, Attitude, Communications) is an
instance of this template trained from its respective YAML config.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.3)
Status:  complete — PyTorch LSTM-AE encoder-decoder with train/reconstruct/error/save/load.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from libs.contracts import TelemetryWindow


class _LSTMEncoderDecoder(nn.Module):
    """PyTorch Sequence-to-Sequence Autoencoder."""

    def __init__(
        self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, latent_dim: int = 32
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.latent_dim = latent_dim

        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc_latent = nn.Linear(hidden_dim, latent_dim)

        # Decoder
        self.fc_decode = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.output_layer = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch_size, seq_len, input_dim)
        batch_size, seq_len, _ = x.shape

        # Encode
        _, (h_n, _) = self.encoder_lstm(x)
        last_hidden = h_n[-1]  # (batch_size, hidden_dim)
        latent = self.fc_latent(last_hidden)  # (batch_size, latent_dim)

        # Decode
        decoder_input = self.fc_decode(latent)  # (batch_size, hidden_dim)
        decoder_input = decoder_input.unsqueeze(1).repeat(
            1, seq_len, 1
        )  # (batch, seq_len, hidden_dim)

        dec_out, _ = self.decoder_lstm(decoder_input)
        reconstruction = self.output_layer(dec_out)  # (batch, seq_len, input_dim)
        return reconstruction


class LSTMAETemplate:
    """
    Parameterised LSTM Autoencoder specialist detector for satellite telemetry.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        model_cfg = config.get("model", {})
        self.channels: list[str] = sorted(config.get("channels", []))

        if not self.channels:
            raise ValueError("LSTMAETemplate config must specify non-empty 'channels' list.")

        self.input_dim = len(self.channels)
        self.hidden_dim = int(model_cfg.get("lstm_hidden_size", 64))
        self.num_layers = int(model_cfg.get("lstm_num_layers", 2))
        self.latent_dim = int(model_cfg.get("latent_dim", 32))
        self.default_epochs = int(model_cfg.get("epochs", 20))
        self.default_batch_size = int(model_cfg.get("batch_size", 32))
        self.default_lr = float(model_cfg.get("learning_rate", 1e-3))

        # Use GPU (RTX 4050) if available, else CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _LSTMEncoderDecoder(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            latent_dim=self.latent_dim,
        ).to(self.device)

        self.is_trained: bool = False

    def _window_to_array(self, window: TelemetryWindow) -> np.ndarray:
        """Convert window channels into (seq_len, input_dim) array in canonical channel order."""
        seq_len = window.window_length
        matrix = np.zeros((seq_len, self.input_dim), dtype=np.float32)
        for col_idx, ch in enumerate(self.channels):
            series = window.channels.get(ch, [0.0] * seq_len)
            matrix[:, col_idx] = series
        return matrix

    def train(
        self,
        train_windows: list[TelemetryWindow],
        epochs: int | None = None,
        batch_size: int | None = None,
        learning_rate: float | None = None,
    ) -> list[float]:
        """
        Train the autoencoder on normal healthy windows using MSE loss.

        Returns:
            list of average loss values per epoch.
        """
        if not train_windows:
            raise ValueError("Cannot train LSTMAETemplate with empty training windows.")

        n_epochs = epochs or self.default_epochs
        b_size = batch_size or self.default_batch_size
        lr = learning_rate or self.default_lr

        # Stack into tensor (num_windows, seq_len, input_dim)
        data_arrays = [self._window_to_array(w) for w in train_windows]
        X = torch.tensor(np.stack(data_arrays), dtype=torch.float32)

        dataset = TensorDataset(X)
        loader = DataLoader(dataset, batch_size=b_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        loss_history: list[float] = []

        for _ in range(n_epochs):
            epoch_loss = 0.0
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                optimizer.zero_grad()
                recon = self.model(batch_x)
                loss = criterion(recon, batch_x)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * batch_x.size(0)

            avg_loss = epoch_loss / len(train_windows)
            loss_history.append(avg_loss)

        self.is_trained = True
        return loss_history

    def reconstruct(self, window: TelemetryWindow) -> np.ndarray:
        """Return the reconstructed sequence array of shape (seq_len, input_dim)."""
        self.model.eval()
        arr = self._window_to_array(window)
        tensor_in = torch.tensor(arr, dtype=torch.float32).unsqueeze(0).to(self.device)
        with torch.no_grad():
            tensor_out = self.model(tensor_in)
        return tensor_out.squeeze(0).cpu().numpy()

    def reconstruction_error(self, window: TelemetryWindow) -> float:
        """Return the overall Mean Squared Error for the window across all channels."""
        arr = self._window_to_array(window)
        recon = self.reconstruct(window)
        return float(np.mean((arr - recon) ** 2))

    def channel_reconstruction_errors(self, window: TelemetryWindow) -> dict[str, float]:
        """Return MSE per individual channel to identify responsible channels."""
        arr = self._window_to_array(window)
        recon = self.reconstruct(window)
        sq_err = (arr - recon) ** 2  # (seq_len, input_dim)
        channel_errors: dict[str, float] = {}
        for col_idx, ch in enumerate(self.channels):
            channel_errors[ch] = float(np.mean(sq_err[:, col_idx]))
        return channel_errors

    def save(self, path: Path) -> None:
        """Persist model weights and configuration to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "config": self.config,
                "is_trained": self.is_trained,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path, config: dict[str, Any] | None = None) -> LSTMAETemplate:
        """Load model from saved checkpoint."""
        checkpoint = torch.load(path, map_location="cpu")
        loaded_config = config or checkpoint.get("config", {})
        instance = cls(loaded_config)
        instance.model.load_state_dict(checkpoint["state_dict"])
        instance.is_trained = checkpoint.get("is_trained", True)
        return instance
