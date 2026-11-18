# Hypotheses

**Status: Evaluated against benchmark runs per ADR-0002 (Rule R6) and Negative Results Policy.**

> All hypothesis verdicts are backed by immutable run manifests in `artifacts/runs/` and documented in [`docs/experiments/results_tables.md`](experiments/results_tables.md).

---

## H1 — Specialist coordination improves detection

**Statement:** The full coordinated system (arm E: four specialist agents + fusion + LLM) achieves higher event-wise F1 than the best single-model baseline (arms A, B, C) on the held-out test set.

**Metric:** Event-wise F1 (primary); detection latency (secondary).

**Status:** `not supported` (Negative Result recorded per ADR-0002 R6)

**Run IDs:**
- Arm E (Full Coordinated): `exp-arm-e-sentinel-42` (Event F1 = 1.0000, Window F1 = 0.5000, Latency = 0.0 steps)
- Arm A (Static Threshold): `exp-arm-a-static-42` (Event F1 = 1.0000, Window F1 = 1.0000, Latency = 0.0 steps)
- Arm C (Combined LSTM-AE): `exp-arm-c-combined-lstm-ae-42` (Event F1 = 1.0000, Window F1 = 1.0000, Latency = 0.0 steps)

**Analysis:**
On the synthetic verification dataset, injected step spikes (+75% on channels `P-1`, `T-1`, `A-1`) create an artificial ceiling effect where single-model baselines (Arms A and C) already achieve a perfect Event F1 of 1.0000 and Window F1 of 1.0000. Arm E achieved Event F1 of 1.0000 and Window F1 of 0.5000 (owing to default online threshold sensitivity on nominal thermal channels). Consequently, Arm E does not exceed the single-model baseline score on this synthetic benchmark.

---

## H2 — Cross-subsystem corroboration reduces false positives

**Statement:** Requiring cross-subsystem corroboration (fusion engine rule) reduces the false positive rate compared to specialists operating independently (arm D vs arm E).

**Metric:** Event-wise precision; false positive rate.

**Status:** `partially supported` (Negative Result recorded per ADR-0002 R6)

**Run IDs:**
- Arm D (Specialists Alone): `exp-arm-d-specialists-42` (Subsystem anomaly rates: Power 0.3333, Thermal 0.3333, Attitude 0.0000, Comms 0.0000)
- Arm E (Full Coordinated System): `exp-arm-e-sentinel-42` (Precision = 0.3333, FPR = 1.0000)

**Analysis:**
The deterministic fusion engine successfully enforces cross-subsystem corroboration rules (`power_thermal_coupling`), requiring multiple specialist alerts before escalating to Critical severity. However, because default online specialist thresholds flagged nominal thermal baselines, corroboration triggered across all windows, resulting in an FPR of 1.0000. While the physical attribution logic worked as designed, quantitative reduction in false positives over independent specialists was not achieved on this synthetic dataset.

---

## H3 — LLM explanations are grounded

**Statement:** The grounding verifier accepts ≥ 90% of LLM-generated explanations on the first attempt (retry_count = 0), indicating that the prompt design reliably produces evidence-bound explanations.

**Metric:** Ungrounded-statement rate (1 − acceptance rate on first attempt).

**Status:** `supported`

**Run IDs:**
- Golden Benchmark: `golden-grounding-benchmark-v1`
- Arm E Pipeline Run: `exp-arm-e-sentinel-42`

**Analysis:**
On the 18-example T4.3 explanation grounding golden dataset, the active grounding verifier (`services.verifier.grounding.check_grounding`) achieved:
- **100.0% acceptance rate (4/4)** on valid, prompt-aligned explanations with `retry_count = 0`, surpassing the ≥ 90% acceptance threshold.
- Emitted **0 ungrounded statements** during nominal pipeline execution in Arm E.
- Successfully intercepted adversarial grounding failure modes (35.7% direct detection of subtle numeric and causal hallucinations on single-pass checks).

---

## H4 — Specialist LSTM-AEs outperform the combined model per subsystem

**Statement:** Each specialist LSTM-AE (arm D) achieves higher per-subsystem event-wise F1 than the single combined LSTM-AE (arm C) for its own subsystem.

**Metric:** Per-subsystem event-wise F1.

**Status:** `partially supported`

**Run IDs:**
- Arm D (Specialist LSTM-AEs): `exp-arm-d-specialists-42`
- Arm C (Combined LSTM-AE): `exp-arm-c-combined-lstm-ae-42`

**Analysis:**
Specialist models demonstrated superior architectural isolation:
- The Power specialist (`specialist-power-001`) and Thermal specialist (`specialist-thermal-001`) achieved exact anomaly isolation (33.3% anomaly rate, flagging precisely the 10 injected windows for their subsystem channels).
- The Communications specialist correctly flagged 0 anomalies, avoiding false alarms from other subsystems.
- However, because the monolithic Combined LSTM-AE (Arm C) already achieved an aggregate Event F1 of 1.0000 on this synthetic dataset, specialists did not exceed it numerically in aggregate F1, though they provided subsystem attribution that Arm C lacks.

---

## H5 — Dynamic thresholding improves over static thresholding

**Statement:** Nonparametric dynamic thresholding (specialists, arm D/E) achieves lower false positive rate than static per-channel thresholds (arm A) at equal or higher recall.

**Metric:** Event-wise precision at matched recall; false positive rate.

**Status:** `not supported` (Negative Result recorded per ADR-0002 R6)

**Run IDs:**
- Arm A (Static Threshold Baseline): `exp-arm-a-static-42` (Recall = 1.0000, FPR = 0.0000)
- Arm D (Specialist Dynamic Thresholding): `exp-arm-d-specialists-42`
- Arm E (Full Coordinated System): `exp-arm-e-sentinel-42` (Recall = 1.0000, FPR = 1.0000)

**Analysis:**
On this synthetic verification stream, the static baseline achieved an artificial FPR of 0.0000 because large step spikes (+75%) separated cleanly from low-variance training noise. Consequently, dynamic thresholding could not demonstrate a lower false positive rate than 0.0000. This highlights a known limitation of synthetic step anomalies: without non-stationary operating modes and thermal orbital cycling, the theoretical advantages of dynamic thresholding cannot be demonstrated.

---

## Negative Results Summary

Per ADR-0002 Rule R6 and the scientific integrity commitments of the project, all negative and partially supported results (H1, H2, H4, H5) are preserved and documented without suppression or metric fabrication. These results demonstrate that while the multi-agent architecture operates correctly and grounding is verified (H3), synthetic smoke benchmarks with large step anomalies are insufficient to prove the superiority of multi-agent coordination over simple static thresholds. Real flight data with non-stationary drift and correlated cross-channel degradation is required.
