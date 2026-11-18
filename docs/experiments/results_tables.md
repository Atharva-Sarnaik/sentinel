# SENTINEL — T4.4 Experimental Results & Evaluation Tables

**Project:** Multi-Agent AI System for Satellite Telemetry Health Monitoring and Anomaly Detection
**Task:** T4.4 — Run Experiments & Results Tables
**Branch:** `main`
**Owner:** Sujal Hede (`@Sujalhede`) / Atharva Sarnaik (`@Atharva-Sarnaik`)
**Timestamp:** 2026-11-16 10:17:46Z
**Status:** All Five Experimental Arms (A–E) Executed & Evaluated

---

## 1. Experimental Setup & Protocol (Synthetic Standard Benchmark)

> **DATA PROVENANCE NOTICE: SYNTHETIC DATASET ONLY**
> All evaluation runs documented here use the **`Synthetic-Standard-Verification`** telemetry stream.
> - **50 training windows** are synthetic, generated with baseline noise to represent nominal satellite operations.
> - **30 evaluation windows** are synthetic, with 10 anomalous windows injected with step spikes (+75%) into channels `P-1`, `T-1`, and `A-1`.
> - **Random Seed:** 42 across Python, NumPy, and PyTorch for exact determinism.
> - **Scope:** This experiment is a **reproducible synthetic benchmark** to verify execution pipelines, manifest persistence, and baseline mechanics across the repository.
> - **Benchmark Limitation:** **This is NOT an actual NASA SMAP/MSL benchmark evaluation.** Physical telemetry from NASA SMAP/MSL is DVC-tracked (`data/README.md`) and, per ADR-0001 and T0.5 findings, lacks verified cross-channel temporal alignment. Synthetic performance must not be construed as NASA flight benchmark performance.

Experiments evaluate anomaly detection across the five Sentinel architectural arms defined in **ADR-0002 (Rule R5)** and tracked in [`docs/HYPOTHESES.md`](../../docs/HYPOTHESES.md):
- **Arm A:** Static per-channel threshold baseline (`services/baselines/static_threshold.py`)
- **Arm B:** Isolation Forest baseline (`services/baselines/isolation_forest.py`)
- **Arm C:** Single combined monolithic LSTM-AE (`services/baselines/combined_lstm_ae.py`)
- **Arm D:** Four specialist LSTM-AE agents alone (`services/specialists/`)
- **Arm E:** Full coordinated multi-agent system (Specialists + Fusion + LLM + Verifier)

### Chronological Data Separation & Splitting
- **Training Set:** 50 chronological healthy telemetry windows reserved strictly for fitting thresholds and training autoencoders. Each window lasts 4 minutes at a 5-minute stride (spanning `t0` to `t0 + 249 min`). No test observations are accessed during training.
- **Evaluation Set:** 30 chronological test windows starting at `t0 + 5 hours` (`t0 + 300 min`), containing controlled multi-channel anomalies (spikes on Power `P-1`, Thermal `T-1`, Attitude `A-1`) and nominal windows.
- **Chronological Separation Gap:** There is an exact chronological separation gap of **51 minutes** between the end of the final training window (`t0 + 249 min`) and the start of the first evaluation window (`t0 + 300 min`). No future observations are used to construct earlier windows, and no temporal overlap exists.
- **Channel Coverage:** Evaluated across all 14 canonical telemetry channels (`P-1`..`P-4`, `T-1`..`T-3`, `A-1`..`A-4`, `C-1`, `C-2`, `D-1`).
- **Dataset Content Hash:** All manifests record the deterministic SHA-256 content hash of the generated synthetic dataset (timestamps, channel names, telemetry values, ordering, and labels). This content hash uniquely identifies the synthetic data stream.

---

## 2. Comparative Results Across Experimental Arms

### Window-Level Classification Metrics

| Evaluation Arm | Model Run ID | Precision | Recall | F1-Score | False Positive Rate | Exec Time (s) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Arm A (Static Threshold)** | `exp-arm-a-static-42` | **1.0000** | **1.0000** | **1.0000** | **0.0000** | 0.0279s | Executed |
| **Arm B (Isolation Forest)** | `exp-arm-b-iforest-42` | 0.3333 | 1.0000 | 0.5000 | 1.0000 | 1.3551s | Executed |
| **Arm C (Combined LSTM-AE)** | `exp-arm-c-combined-lstm-ae-42` | **1.0000** | **1.0000** | **1.0000** | **0.0000** | 8.1496s | Executed |
| **Arm D (Specialists Alone)** | `exp-arm-d-specialists-42` | — | — | — | — | 3.8248s | Executed (Per-Subsystem) |
| **Arm E (Full Coordinated)** | `exp-arm-e-sentinel-42` | 0.3333 | **1.0000** | 0.5000 | 1.0000 | 1.1751s | Executed |

### Headline Event-Wise Metrics (ADR-0002 Rule R4)

| Evaluation Arm | Event Precision | Event Recall | Event F1 | Mean Detection Latency | Point-Adjusted F1 (Labelled Comparison) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Arm A (Static Threshold)** | **1.0000** | **1.0000** | **1.0000** | **0.0 steps** | 1.0000 |
| **Arm B (Isolation Forest)** | 1.0000 | 1.0000 | 1.0000 | 0.0 steps | 0.5000 |
| **Arm C (Combined LSTM-AE)** | **1.0000** | **1.0000** | **1.0000** | **0.0 steps** | 1.0000 |
| **Arm E (Full Coordinated)** | 1.0000 | **1.0000** | 1.0000 | 0.0 steps | 0.5000 |

---

## 3. Results Interpretation & Architectural Analysis

### Arm A (Static Threshold Baseline)
- **Result:** Precision = 1.0000, Recall = 1.0000, F1 = 1.0000, FPR = 0.0000.
- **Interpretation:** The perfect F1-score is an artifact of the synthetic smoke test. Injected anomalies are step spikes of +75% over baseline, which easily exceed the 99.5th percentile upper threshold fitted on low-variance synthetic training noise. **This perfect score is not evidence of generalization to real satellite telemetry**, where baseline drift, seasonal shifts, and non-stationary operating modes routinely confound static thresholds.

### Arm B (Isolation Forest Baseline)
- **Result:** Precision = 0.3333, Recall = 1.0000, F1 = 0.5000, FPR = 1.0000.
- **Interpretation:** The false-positive rate is 1.0000 because the baseline decision logic in `services/baselines/isolation_forest.py` maps raw `-score_samples()` to an anomaly score in `[0.0, 1.0]` and hardcodes `if anomaly_score >= 0.5: severity = WARNING`. On this low-variance synthetic data, nominal windows produce scores slightly above 0.50, causing every evaluation window to be flagged as anomalous.

### Arm C (Combined Monolithic LSTM-AE)
- **Result:** Precision = 1.0000, Recall = 1.0000, F1 = 1.0000, FPR = 0.0000.
- **Interpretation:** Arm C achieves a perfect F1-score on the synthetic test set because large injected step spikes (+75% on `P-1`, `T-1`, `A-1`) create massive reconstruction errors that overwhelmingly surpass the dynamic MSE threshold (`622.99`).

### Arm D (Specialist LSTM-AEs Alone)
- **Result:** Evaluated per-subsystem (Power, Thermal, Attitude, Communications).
- **Interpretation:** Unsupervised anomaly statistics (`threshold`, `anomaly_rate`, `mean_anomaly_score`, `reconstruction_error`) are computed by `services/specialists/train.py`.

### Arm E (Full Coordinated Multi-Agent System)
- **Result:** Precision = 0.3333, Recall = 1.0000, F1 = 0.5000, FPR = 1.0000.
- **Model Run ID:** `exp-arm-e-sentinel-42`
- **Interpretation:** Arm E runs the complete compiled LangGraph state graph end-to-end (`specialists` → `fusion` → `reasoner` → `verifier` → `audit`). The default online specialist threshold (`abs(x) > 40.0`) flagged `T > 40` across nominal thermal windows, which the power-thermal coupling rule escalated to Critical alert level. This real empirical result is recorded honestly per ADR-0002 R6.

---

## 4. Arm D: Per-Subsystem Specialist Performance

Specialist LSTM-AE models trained from YAML configurations (`services/specialists/configs/*.yaml`):

| Subsystem | Specialist Model | Channels | Calibrated Dynamic Threshold | Anomaly Rate | Mean Anomaly Score |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Power** | `specialist-power-001` | P-1, P-2, P-3, P-4 | 798.7938 | 0.3333 | 0.5503 |
| **Thermal** | `specialist-thermal-001` | T-1, T-2, T-3 | 2047.2401 | 0.3333 | 0.5701 |
| **Attitude** | `specialist-attitude-001` | A-1, A-2, A-3, A-4 | 1.5647 | 0.0000 | 0.3344 |
| **Communications** | `specialist-communications-001` | C-1, C-2, D-1 | 27.0553 | 0.0000 | 0.4354 |

---

## 5. T4.3 Explanation Grounding Benchmark Status

The explanation grounding evaluation dataset was evaluated against the active Tier 3 grounding verifier (`services.verifier.grounding.check_grounding`):
- **Total Labelled Examples:** 18
- **Ground-Truth Grounded:** 4 (Positive cases)
- **Ground-Truth Ungrounded:** 14 (Negative cases across 7 failure modes)
- **Grounded Acceptance Rate:** **100.0%** (4/4 valid prompt outputs verified)
- **Ungrounded Rejection Rate:** **35.7%** (Adversarial grounding failures intercepted)
- **Overall Verifier Accuracy:** **50.0%**
- **Categories Verified:** contradiction_with_evidence, fully_grounded, incorrect_subsystem_attribution, invented_telemetry_observation, missing_causal_evidence, partially_grounded, unsupported_anomaly_severity, unsupported_numerical_claim

---

## 6. Documented Limitations & Data Notes

1. **NASA SMAP/MSL DVC Dataset Access:**
   - Raw and processed datasets are excluded from git and tracked via DVC (`data/README.md`). Local workspace does not contain pulled DVC raw arrays.
   - Per ADR-0001 and T0.5 research, channel streams have independent sampling rates and lack physical synchronization. Experiments used the `Synthetic-Standard-Verification` stream to prevent unverified temporal alignment.

---

## 7. Reproduction Commands

To reproduce all experimental runs and regenerate the run manifests and metrics:

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Execute experiment runner across all 5 arms
python scripts/run_experiments.py

# Inspect generated run manifests
sentinel specialists-report latest
```