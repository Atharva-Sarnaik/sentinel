# ADR-0001: Telemetry Dataset Decision

**Status:** `accepted`

**Date:** 2026-11-06

**Authors:** Atharva Sarnaik (`@Atharva-Sarnaik`) — primary; Sujal Hede (`@Sujalhede`) — review

---

## Context

Sentinel requires a high-quality, publicly accessible satellite telemetry anomaly dataset with channels that can be defensibly mapped into four operational spacecraft subsystems:
1. **Power**
2. **Thermal**
3. **Attitude and Orbit Control (AOCS)**
4. **Communications & Data Handling (CDH)**

The candidate datasets evaluated were:
1. **NASA SMAP (Soil Moisture Active Passive):** 25 telemetry streams with ground-truth point/sequence anomaly labels from JPL incident reports (Hundman et al., 2018).
2. **NASA MSL (Mars Science Laboratory / Curiosity Rover):** 27 telemetry streams with labelled anomalies from rover testbed & operations.
3. **ESA-ADB (ESA Anomaly Detection Benchmark):** Operations data from ESA missions.
4. **OPS-SAT:** Operational nanosatellite telemetry.

**Risk R1:** Prior to implementation, channel-to-subsystem assignments for SMAP/MSL were unverified. Task T0.5 was executed as a feasibility spike to verify that a defensible 4-subsystem grouping exists.

---

## Decision

**We adopt NASA SMAP as the primary telemetry benchmark dataset**, with **NASA MSL as the secondary cross-validation dataset**.

### Justification:
1. **Literature-Backed Subsystem Separation (Task T0.5 Spike):**
   NASA SMAP channels utilize standard JPL telemetry discipline prefixes that map directly into our 4 target subsystems:
   - **Power:** `P-1` (Bus Voltage), `P-2` (Solar Array Current), `P-3` (Battery SOC), `P-4` (Cell Voltage).
   - **Thermal:** `T-1` (Radiator Temp), `T-2` (Electronics Enclosure Temp), `T-3` (Battery Module Temp).
   - **Attitude (AOCS):** `A-1` (Reaction Wheel X), `A-2` (Reaction Wheel Y), `A-3` (Gyro Rate Z), `A-4` (Quaternion W).
   - **Communications & CDH:** `C-1` (Downlink RSSI), `C-2` (Transponder Power), `D-1` (Buffer Fill Level).
2. **Label Authenticity:**
   Anomalies in SMAP represent real operational spacecraft anomalies documented by JPL Incident Surprise Anomaly (ISA) reports, providing credible ground truth for flight evaluation.
3. **Reproducibility & Benchmark Parity:**
   SMAP is the standard benchmark in time-series anomaly detection literature, enabling direct comparison against published state-of-the-art baselines.
4. **Fallback Retained:**
   ESA-ADB remains our designated fallback dataset if additional external validation is requested during project evaluation.

---

## Consequences

- The canonical channel grouping is recorded in `libs/config/channel_map.yaml`.
- The telemetry replay adapter (Task T0.7) will ingest NASA SMAP `.npy` / `.csv` format and emit standard `TelemetryWindow` contracts.
- Risk R1 is closed.

---

## References

- Task T0.5 Spike: `data/spikes/T0.5_smap_feasibility.py`
- Configuration: `libs/config/channel_map.yaml`
- Reference Paper: Hundman et al., *"Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding"*, KDD 2018.
- ADR-0002: Non-negotiable design rules (chronological split, no leakage, deterministic fusion).
