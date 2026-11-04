# evaluation

**Purpose:** Evaluation metrics, ablation harness (arms A–E), and golden set for explanation grounding.

**Inputs:** Predicted and ground-truth anomaly events; `VerifierResult` records.

**Outputs:** Metrics tables (event-wise P/R/F1, detection latency, attribution accuracy, ungrounded-statement rate).

**Key modules:**
| Module | Description |
|---|---|
| `metrics.py` | Event-wise metrics, latency, attribution accuracy (T4.1) |
| `ablation.py` | Harness for arms A–E on identical windows (T4.2) |
| `golden_set/` | Labelled windows for grounding evaluation (T4.3) |

**Owner:** Atharva Sarnaik (`@Atharva-Sarnaik`) — metrics, ablation, H1–H5; Sujal Hede (`@Sujalhede`) — golden set, results

**Tier:** 4 | **Tasks:** T4.1–T4.5

**Status:** `not started`

> **Design rule (ADR-0002):** Point-adjusted scores may be reported only as a labelled comparison, never as the headline metric.

