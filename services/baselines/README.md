# baselines

**Purpose:** Three evaluation baselines for the ablation study (arms A, B, C).

**Inputs:** Normalised `TelemetryWindow` from `feature_plane`.

**Outputs:** `libs.contracts.SpecialistOpinion`.

**Arms:**
| Arm | Module | Description | Owner | Task |
|---|---|---|---|---|
| A | `static_threshold.py` | Fixed per-channel thresholds | Sujal | T1.1 |
| B | `isolation_forest.py` | Isolation Forest | Sujal | T1.2 |
| C | `combined_lstm_ae.py` | Single combined LSTM-AE | Atharva | T1.6 |

**Tier:** 1 | **Status:** `not started`

