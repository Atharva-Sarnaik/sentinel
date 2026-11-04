# Hypotheses

**Status: all hypotheses are `untested`. No experimental results exist yet.**

> No hypothesis status may be changed from `untested` without a valid MLflow/DVC run ID attached to the update (ADR-0002, Rule R6).

---

## H1 — Specialist coordination improves detection

**Statement:** The full coordinated system (arm E: four specialist agents + fusion + LLM) achieves higher event-wise F1 than the best single-model baseline (arms A, B, C) on the held-out test set.

**Metric:** Event-wise F1 (primary); detection latency (secondary).

**Status:** `untested`

**Run ID:** —

---

## H2 — Cross-subsystem corroboration reduces false positives

**Statement:** Requiring cross-subsystem corroboration (fusion engine rule) reduces the false positive rate compared to specialists operating independently (arm D vs arm E).

**Metric:** Event-wise precision; false positive rate.

**Status:** `untested`

**Run ID:** —

---

## H3 — LLM explanations are grounded

**Statement:** The grounding verifier accepts ≥ 90% of LLM-generated explanations on the first attempt (retry_count = 0), indicating that the prompt design reliably produces evidence-bound explanations.

**Metric:** Ungrounded-statement rate (1 − acceptance rate on first attempt).

**Status:** `untested`

**Run ID:** —

---

## H4 — Specialist LSTM-AEs outperform the combined model per subsystem

**Statement:** Each specialist LSTM-AE (arm D) achieves higher per-subsystem event-wise F1 than the single combined LSTM-AE (arm C) for its own subsystem.

**Metric:** Per-subsystem event-wise F1.

**Status:** `untested`

**Run ID:** —

---

## H5 — Dynamic thresholding improves over static thresholding

**Statement:** Nonparametric dynamic thresholding (specialists, arm D/E) achieves lower false positive rate than static per-channel thresholds (arm A) at equal or higher recall.

**Metric:** Event-wise precision at matched recall; false positive rate.

**Status:** `untested`

**Run ID:** —

---

## Negative Results Policy

Negative results (a hypothesis not supported by experimental data) must be reported fully, including the run ID, metric table, and analysis. They must not be omitted from the final report (task T4.5).

