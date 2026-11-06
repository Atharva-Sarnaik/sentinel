# Sentinel — Roles and Task Distribution Guide

> **Project:** Multi-Agent AI System for Satellite Telemetry Health Monitoring and Anomaly Detection  
> **Institution:** Government College of Engineering, Kolhapur — Dept. of AI & Data Science (BE 2026–2027)  
> **Team:** Atharva Sarnaik (`@Atharva-Sarnaik`), Sujal Hede (`@Sujalhede`)  
> **Guide:** Dr. M. S. Arade  

---

## 1. High-Level Summary

| Role Track | Primary Owner | Scope & Focus | Key Deliverables |
|---|---|---|---|
| **Role A: Fusion Engine, Orchestration, Evaluation, CI** | **Atharva Sarnaik** | Multi-agent coordinator brain, LLM reasoning, hallucination verification, scientific benchmarks, CI/CD code quality. | LangGraph pipeline, deterministic fusion engine, prompt templates & grounding verifier, evaluation ablation harness (Arms A–E). |
| **Role B: Data Plane, Feature Plane, Specialists, API** | **Sujal Hede** | Data ingestion, signal normalization, deep learning model training for 4 subsystems, database logging, APIs & dashboards. | SMAP/MSL replay adapter, 4 trained LSTM-Autoencoder models, SQLite audit logger, FastAPI service, Streamlit dashboard. |

> **Backup / Pair Policy:** If any task under Sujal's track requires extra bandwidth or is delayed, Atharva will step in to pair-program or implement that specific task when called out.

---

## 2. Detailed Breakdown: Role A (Atharva Sarnaik)

### Core Mission
Build the multi-agent coordinator brain, enforce zero hallucinations through strict grounding verification, run the scientific ablation evaluation comparing Sentinel against baselines, and maintain developer tooling.

### Tier-by-Tier Tasks:
* **Tier 0: Foundations (Weeks 1–6)**
  * **T0.2:** Branch protection, CODEOWNERS configuration, and GitHub Actions CI green verification.
  * **T0.3:** Core contracts library — frozen Pydantic v2 data models (`TelemetryWindow`, `SpecialistOpinion`, `FusionDecision`, `Explanation`, `VerifierResult`, `AuditEntry`, `RunManifest`).
  * **T0.6:** ADR-0001 dataset decision document (evaluating NASA SMAP/MSL vs ESA-ADB).
  * **T0.8:** Telemetry data-integrity gate (`services/data_plane/integrity_gate.py`) for range, schema, and staleness validation.
  * **T0.10:** Permanent data leakage regression suite (`tests/leakage/test_leakage.py`) to prevent look-ahead bias in time series.

* **Tier 1: Specialists & Baselines (Weeks 7–11)**
  * **T1.4:** Nonparametric dynamic thresholding module (`services/specialists/thresholding.py`) for anomaly scoring.
  * **T1.6:** Baseline Arm C — single combined LSTM-Autoencoder model taking all telemetry channels simultaneously.
  * **T1.7:** MLflow model registry and experiment tracking setup (logging runs, hyperparameters, loss curves, artifacts).

* **Tier 2: Fusion Engine (Weeks 12–14)**
  * **T2.1:** Severity weighting logic (`services/fusion/engine.py`) ensuring deterministic assignment (NOMINAL, ADVISORY, WARNING, CRITICAL).
  * **T2.2:** Cross-subsystem corroboration rules (e.g., escalating severity when Power voltage drop coincides with Thermal spike).

* **Tier 3: Orchestration, Reasoner, Verifier, Audit (Weeks 15–17)**
  * **T3.1:** LangGraph StateGraph orchestration pipeline (`services/orchestrator/graph.py`) coordinating parallel specialists, join, fusion, and verification.
  * **T3.2:** LLM reasoner and prompt engineering (`services/reasoner/`) producing structured flight-controller explanations with GPT-4o-mini.
  * **T3.4:** Retry policy and abstention path (`services/verifier/retry.py`) allowing max 2 retries on ungrounded claims before abstaining with an evidence-only report.
  * **T3.6:** Observability and tracing (`services/observability/tracing.py`) using Langfuse for token cost and latency tracking.

* **Tier 4: Evaluation and Ablation (Weeks 18–20)**
  * **T4.1:** Evaluation metrics implementation (`services/evaluation/metrics.py`) for event-wise Precision/Recall/F1, detection latency, and attribution accuracy.
  * **T4.2:** Ablation harness (`services/evaluation/ablation.py`) executing all five evaluation arms (A to E) on identical test windows.
  * **T4.5:** Hypotheses analysis and updating verdicts for H1–H5 in `docs/HYPOTHESES.md`.

* **Tier 5–7: Interfaces, Extensions & Defense (Weeks 21–28)**
  * **T5.1 & T5.4:** Typer + Rich CLI commands (`sentinel analyze`, `evaluate`, `report`) and one-command clean clone demo script.
  * **T6.2:** *(Extended)* Learned stacking coordinator compared against deterministic rule-based fusion.
  * **T6.3:** *(Extended)* QLoRA fine-tune of a small local open-weights model on laptop RTX 4050 compared against cloud API.
  * **T7.1:** CI hardening and strict test coverage gates.
  * **T7.4:** Viva defense cross-rehearsal.

---

## 3. Detailed Breakdown: Role B (Sujal Hede)

### Core Mission
Build the data ingestion and time-series extraction pipeline, train the 4 specialist LSTM neural networks for each satellite subsystem, manage the audit database, and build the Web API & interactive dashboard.

### Tier-by-Tier Tasks:
* **Tier 0: Foundations (Weeks 1–6)**
  * **T0.1:** Local developer environment bootstrap, Makefile, and PowerShell `check.ps1` verification.
  * **T0.4:** Configuration schema and validating loader (`libs/config/loader.py` + `channel_map.yaml`).
  * **T0.5:** Risk R1 feasibility spike — Jupyter notebook analyzing NASA SMAP/MSL channel groupings into 4 subsystems.
  * **T0.7:** Telemetry replay adapter (`services/data_plane/adapter.py`) streaming historical data in chronological sequence.
  * **T0.9:** Windowing and chronological split (`services/feature_plane/`) with sliding windows and z-score normalization fit on train partition only.

* **Tier 1: Specialists & Baselines (Weeks 7–11)**
  * **T1.1:** Baseline Arm A — static per-channel threshold detection.
  * **T1.2:** Baseline Arm B — Isolation Forest anomaly detection model using scikit-learn.
  * **T1.3:** Shared PyTorch LSTM-Autoencoder template (`services/specialists/lstm_ae_template.py`).
  * **T1.5:** Train the four specialist models (Power, Thermal, Attitude, Communications) and compile subsystem performance metrics.
  * **T1.8:** Specialist report CLI command (`sentinel specialists-report`).

* **Tier 2: Fusion Engine (Weeks 12–14)**
  * **T2.3:** Subsystem attribution logic matching anomalies to responsible channels.
  * **T2.4:** Golden test cases and property-based tests for deterministic fusion decisions.

* **Tier 3: Orchestration, Reasoner, Verifier, Audit (Weeks 15–17)**
  * **T3.3:** Grounding verifier check (`services/verifier/grounding.py`) validating that LLM citations strictly exist within fusion evidence.
  * **T3.5:** Immutable audit log writer (`services/audit/log_writer.py`) persisting records to SQLite/PostgreSQL before action is taken.

* **Tier 4: Evaluation and Ablation (Weeks 18–20)**
  * **T4.3:** Golden labelled evaluation dataset committed for explanation grounding benchmarks.
  * **T4.4:** Experiment execution and population of raw metrics and run IDs into results tables.

* **Tier 5–7: Interfaces, Extensions & Defense (Weeks 21–28)**
  * **T5.2:** FastAPI web service (`services/api/app.py`) providing typed endpoints for analysis and run retrieval.
  * **T5.3:** HTML and JSON report export generation.
  * **T6.1:** *(Extended)* Streamlit interactive replay dashboard showing 4 subsystem panels and coordinator view.
  * **T6.4:** *(Extended)* Docker Compose multi-container stack deployment.
  * **T7.2 & T7.3:** Model cards authoring and final project report compilation.
  * **T7.4:** Viva defense cross-rehearsal.

---

## 4. Key Collaboration Points

```
[Raw Telemetry Ingestion (Role B)]
                │
                ▼
[Feature Windowing & Splits (Role B)] ───► [Integrity Gate Check (Role A)]
                │
                ▼
[4 Specialist LSTM-AEs (Role B)] ────────► [Dynamic Thresholding (Role A)]
                │
                ▼ (SpecialistOpinion objects)
[Deterministic Fusion Engine (Role A)] ──► [Attribution Logic (Role B)]
                │
                ▼ (FusionDecision evidence)
[LLM Reasoner (Role A)] ─────────────────► [Grounding Verifier (Role B & A)]
                │
                ▼ (Grounded Explanation)
[Audit Log DB Writer (Role B)] ──────────► [FastAPI & Streamlit UI (Role B)]
                                         ► [Ablation Benchmark Suite (Role A)]
```

---

## 5. Viva Defense Strategy

* **Atharva defends:** Multi-agent design decisions, why deterministic fusion governs alert severity rather than generative LLMs, how the grounding verifier mathematically prevents hallucinations, and the event-wise F1-score gains across the 5 ablation arms.
* **Sujal defends:** Time-series feature engineering, prevention of chronological look-ahead leakage, LSTM-Autoencoder reconstruction mechanics, threshold calibration per subsystem, and real-time dashboard latency.
* **Cross-defense (T7.4):** In the final two weeks, both teammates rehearse explaining each other’s code so there are no single points of failure in the viva.
