# Sentinel Command-Line Interface (CLI) Guide

**Version:** 0.1.0  
**Entry Point:** `sentinel` or `python -m apps.cli.main`

---

## 1. Overview

Sentinel provides a command-line interface powered by [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/) for operator telemetry health analysis, ablation evaluations, and experiment report generation.

```powershell
# Display top-level CLI commands and options
sentinel --help
```

---

## 2. Available Commands

### 2.1 `sentinel analyze`

Run the complete multi-agent Sentinel pipeline on a telemetry input file or a synthetic sample window.

**Pipeline Flow:**
1. Ingests 14-channel telemetry window.
2. Executes four parallel specialist agents (Power, Thermal, Attitude, Communications).
3. Evaluates deterministic physics fusion rules to determine system severity and attribute root cause.
4. Generates an evidence-bound natural language explanation from the LLM reasoner.
5. Verifies grounding against numerical telemetry citations (max 2 retries, then abstains).
6. Atomically commits an immutable `AuditEntry` to the SQLite audit log.

**Usage Examples:**

```powershell
# Analyze a synthetic sample window with coupled Power and Thermal anomalies
sentinel analyze sample

# Analyze an external telemetry JSON file and export a visual HTML report
sentinel analyze data/sample_window.json --report html --output artifacts/window_analysis.html

# Analyze telemetry and export a structured JSON report for machine consumption
sentinel analyze sample --report json --output artifacts/window_analysis.json --run-id flight-pass-104
```

---

### 2.2 `sentinel evaluate`

Execute the ablation evaluation harness across experimental arms (A through E) on identical chronological telemetry windows.

**Evaluation Arms:**
- **Arm A:** Static per-channel threshold baseline
- **Arm B:** Isolation Forest baseline
- **Arm C:** Combined monolithic LSTM-AE
- **Arm D:** Four specialist LSTM-AE agents operating independently
- **Arm E:** Full coordinated multi-agent system (Sentinel)

**Usage Examples:**

```powershell
# Run all five evaluation arms on the synthetic verification dataset
sentinel evaluate synthetic --arms A,B,C,D,E

# Run single-model baselines only with custom random seed
sentinel evaluate synthetic --arms A,B,C --seed 99
```

---

### 2.3 `sentinel report`

Print or export an analysis or experiment run report from the immutable manifest store (`artifacts/runs/`).

**Usage Examples:**

```powershell
# Export report for the most recent experimental run as JSON
sentinel report latest --fmt json --output artifacts/latest_run_report.json

# Export a visual HTML report for a specific run ID
sentinel report exp-arm-e-sentinel-42 --fmt html --output artifacts/arm_e_report.html
```

---

### 2.4 `sentinel specialists-report`

Print the per-subsystem specialist metrics table, showing calibrated dynamic thresholds, reconstruction losses, anomaly counts, and health statuses.

**Usage Examples:**

```powershell
# Print specialist metrics for the latest training run
sentinel specialists-report latest

# Print specialist metrics for a specific run ID
sentinel specialists-report exp-arm-d-specialists-42
```

---

### 2.5 `sentinel demo`

Run an end-to-end interactive demonstration of the entire Sentinel multi-agent pipeline. Generates sample telemetry, executes all five pipeline stages, verifies grounding and audit logging, and exports both HTML and JSON demo reports to `artifacts/`.

**Usage Example:**

```powershell
sentinel demo
# or:
python scripts/demo.py
```
