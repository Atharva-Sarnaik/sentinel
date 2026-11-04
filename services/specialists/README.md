# specialists

**Purpose:** Four specialist agents (Power, Thermal, Attitude, Communications), each an LSTM Autoencoder parameterised from a per-subsystem YAML config.

**Inputs:** Normalised `TelemetryWindow` from `feature_plane`.

**Outputs:** `libs.contracts.SpecialistOpinion` per subsystem per window.

**Key modules:**
| Module | Description |
|---|---|
| `lstm_ae_template.py` | Shared LSTM-AE model class (T1.3) |
| `thresholding.py` | Nonparametric dynamic thresholding (T1.4) |
| `configs/` | Per-subsystem YAML configs |

**Owner:** Sujal Hede (`@Sujalhede`) — template, training; Atharva Sarnaik (`@Atharva-Sarnaik`) — thresholding

**Tier:** 1 | **Tasks:** T1.3, T1.4, T1.5

**Status:** `not started`

