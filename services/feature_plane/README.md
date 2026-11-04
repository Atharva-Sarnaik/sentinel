# feature_plane

**Purpose:** Transform validated `TelemetryWindow` objects into normalised, feature-ready windows stored in a Parquet + DuckDB feature store.

**Inputs:** `libs.contracts.TelemetryWindow` from `data_plane`.

**Outputs:** Normalised `TelemetryWindow` objects; feature vectors in Parquet; chronological train/test index sets.

**Key modules:**
| Module | Description |
|---|---|
| `windowing.py` | Sliding-window extraction |
| `normalisation.py` | Per-channel z-score (fit on train only) |
| `features.py` | Statistical and temporal feature extraction |
| `splits.py` | Chronological train/test split (no shuffling — ADR-0002) |

**Owner:** Sujal Hede (`@Sujalhede`)

**Tier:** 0 | **Tasks:** T0.9

**Status:** `not started`

> **Design rule (ADR-0002):** Splits are strictly chronological. No random shuffling across the train/test boundary. The leakage regression suite (T0.10) catches any shuffle bug.

