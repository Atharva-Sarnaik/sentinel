# ADR-0002: Non-Negotiable Design Rules

**Status:** `accepted`

**Date:** 2026-11-04

**Authors:** Atharva Sarnaik (`@Atharva-Sarnaik`), Sujal Hede (`@Sujalhede`)

---

## Context

To ensure scientific integrity, reproducibility, and audit-ability of Sentinel as a research prototype, a set of non-negotiable design rules is required. These rules are enforced by import-linter contracts, unit tests, and CI checks.

---

## Rules

### R1 — LLM Role Boundary

> **The LLM never decides severity or alert level. The fusion engine decides; the LLM only explains.**

- `FusionDecision.severity` is set by `services.fusion.engine.fuse()`.
- The LLM receives `FusionDecision` as a **read-only** evidence object.
- The LLM's output (`Explanation`) is a natural-language explanation only.
- The verifier rejects any explanation that escalates or de-escalates severity.

### R2 — Verifier Grounding

> **The verifier rejects any explanation citing a channel, value or severity not present in the evidence object.**

- Implemented in `services.verifier.grounding.check_grounding()`.
- Maximum 2 retries. On third failure, the system **abstains** and emits an evidence-only report.
- `VerifierResult.retry_count` is bounded to [0, 2] by the Pydantic model.

### R3 — Chronological Splits Only

> **No random shuffling across the train/test boundary. Splits are chronological only.**

- Implemented in `services.feature_plane.splits.chronological_split()`.
- The boundary is logged and reproducible given the same config.
- The leakage regression suite (`tests/leakage/`) catches any shuffle bug (task T0.10).

### R4 — Headline Metrics

> **Headline metrics are event-wise precision/recall/F1, detection latency, subsystem attribution accuracy, and ungrounded-statement rate.**

- Point-adjusted scores may be reported **only as a labelled comparison**, never as the headline metric.
- Implemented in `services.evaluation.metrics`.

### R5 — Evaluation Arms

> **Five evaluation arms are always compared: A (static threshold), B (Isolation Forest), C (single combined LSTM-AE), D (specialists alone), E (full coordinated system).**

- Implemented in `services.evaluation.ablation`.
- Arms run on **identical** windows.

### R6 — Hypotheses Tracking

> **Hypotheses H1–H5 are tracked in `docs/HYPOTHESES.md` with status `untested` until real experimental runs exist.**

- No hypothesis may be marked with any other status without a run ID from MLflow/DVC.

### R7 — Audit Before Action

> **Every decision is logged to the audit log (AuditEntry) before any downstream outcome is joined.**

- Implemented in `services.audit.log_writer`.
- AuditEntry is immutable after creation (frozen Pydantic model).

---

## Enforcement

| Rule | Mechanism |
|---|---|
| R1, R2 | Unit tests in `tests/unit/`, grounding tests in `tests/integration/` |
| R3 | `tests/leakage/test_leakage.py` (permanent CI regression) |
| R4, R5 | Metric unit tests on synthetic cases (`tests/unit/`) |
| R6 | PR checklist: "no result claimed without a run ID" |
| R7 | Integration tests for `services.audit` |
| All | import-linter contracts in `pyproject.toml` |

---

## Consequences

- Any PR that violates these rules must be rejected in review.
- Both team members must be able to explain every rule at the viva (task T7.4).

