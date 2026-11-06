# Task Directory

Full task list with IDs, owners, branch names, and done-when criteria.

**Owner key:** **A** = Atharva Sarnaik (`@Atharva-Sarnaik`), **S** = Sujal Hede (`@Sujalhede`)

---

## Tier 0: Foundations (weeks 1–6) — Status: COMPLETED ✅

| ID | Task | Owner | Branch | Status | Done when |
|---|---|---|---|---|---|
| T0.1 | Dev environment, Makefile/PowerShell, README | S | `chore/T0.1-dev-env` | Done | Fresh clone → green checks on both machines |
| T0.2 | Branch protection, CODEOWNERS, CI green | A | `chore/T0.2-branch-protection` | Done | Rules active; CI green on empty repo |
| T0.3 | Contracts library: typed models and tests | A | `feat/T0.3-contracts` | Done | Contracts frozen and unit-tested |
| T0.4 | Config schema incl. channel→subsystem map | S | `feat/T0.4-config-schema` | Done | YAML + validating loader |
| T0.5 | SMAP/MSL feasibility spike (risk R1) | S | `exp/T0.5-smap-feasibility` | Done | Notebook documents whether a defensible 4-subsystem grouping exists |
| T0.6 | ADR-0001 dataset decision | A | `docs/T0.6-adr-dataset` | Done | ADR merged after review |
| T0.7 | Telemetry adapter and replay source | S | `feat/T0.7-telemetry-adapter` | Done | Windows streamed in time order, no future data |
| T0.8 | Data-integrity gate | A | `feat/T0.8-integrity-gate` | Done | Stale or corrupt input rejected with reasons |
| T0.9 | Windowing and chronological split | S | `feat/T0.9-windowing-split` | Done | Split reproducible; boundary test passes |
| T0.10 | Permanent leakage-regression suite | A | `chore/T0.10-leakage-suite` | Done | Planted look-ahead bug caught by CI |

---

## Tier 1: Specialists and Baselines (weeks 7–11) — COMPLETED ✅

| ID | Task | Owner | Status | Done when |
|---|---|---|---|---|
| T1.1 | Static-threshold baseline (arm A) | S | Done | Runs in harness |
| T1.2 | Isolation Forest baseline (arm B) | S | Done | Runs in harness |
| T1.3 | Shared LSTM-AE template and training script | S | Done | One script trains any subsystem from config |
| T1.4 | Nonparametric dynamic thresholding | A | Done | Thresholds produced per channel group |
| T1.5 | Train four specialists, per-subsystem eval | S | Done | Metrics table per subsystem with run IDs |
| T1.6 | Single combined LSTM-AE (arm C) | A | Done | Runs in harness |
| T1.7 | Model registry and experiment tracking (MLflow) | A | Done | Artifacts versioned; runs reference hashes |
| T1.8 | `specialists report` CLI command | S | Done | Prints per-subsystem metrics |

---

## Tier 2: Fusion Engine (weeks 12–14) — COMPLETED ✅

| ID | Task | Owner | Status | Done when |
|---|---|---|---|---|
| T2.1 | Severity weighting | A | Done | Deterministic, documented, unit-tested |
| T2.2 | Cross-subsystem corroboration rules | A | Done | Rules in config, golden-case tests |
| T2.3 | Subsystem attribution logic | S | Done | Attribution output matches contract |
| T2.4 | Fusion golden cases and property tests | S | Done | Same input always gives same decision |

---

## Tier 3: Orchestration, Reasoner, Verifier, Audit (weeks 15–17)

| ID | Task | Owner | Branch | Done when |
|---|---|---|---|---|
| T3.1 | LangGraph skeleton with mock LLM | A | `feat/T3.1-langgraph-skeleton` | Graph runs end-to-end offline |
| T3.2 | LLM reasoner, prompt library, JSON schema | A | `feat/T3.2-llm-reasoner` | Prompts versioned in files; schema-valid output |
| T3.3 | Verifier grounding check | S | `feat/T3.3-verifier-grounding` | Ungrounded claim flagged via `VerifierResult` |
| T3.4 | Retry policy and abstention path | A | `feat/T3.4-retry-abstention` | Max 2 retries, then evidence-only report |
| T3.5 | Audit log | S | `feat/T3.5-audit-log` | Every decision logged before any outcome is joined |
| T3.6 | Tracing, cost and latency logging (Langfuse) | A | `feat/T3.6-langfuse-tracing` | Each LLM call traced |

---

## Tier 4: Evaluation and Ablation (weeks 18–20)

| ID | Task | Owner | Branch | Done when |
|---|---|---|---|---|
| T4.1 | Event-wise metrics, latency, attribution accuracy | A | `feat/T4.1-eval-metrics` | Metrics unit-tested on synthetic cases |
| T4.2 | Ablation harness (arms A–E) | A | `feat/T4.2-ablation-harness` | One command runs all arms on identical windows |
| T4.3 | Golden set for explanation grounding | S | `feat/T4.3-golden-set` | Labelled set committed |
| T4.4 | Run experiments, results tables | S | `feat/T4.4-experiments` | Tables with run IDs and raw metrics |
| T4.5 | H1–H5 verdicts, negative results included | A | `docs/T4.5-hypotheses-verdicts` | `docs/HYPOTHESES.md` updated from real runs |

---

## Tier 5: Interfaces (weeks 21–22)

| ID | Task | Owner | Branch | Done when |
|---|---|---|---|---|
| T5.1 | CLI commands (`analyze`, `evaluate`, `report`) | A | `feat/T5.1-cli-commands` | Documented with examples |
| T5.2 | FastAPI service | S | `feat/T5.2-fastapi` | Typed endpoints, tests |
| T5.3 | HTML/JSON report export | S | `feat/T5.3-report-export` | `analyze --report html` works |
| T5.4 | CLI polish and one-command demo script | A | `feat/T5.4-cli-polish` | Demo runs from a clean clone |

---

## Tier 6: Extended Objectives (weeks 23–26)

> Only if Tier 4 results exist.

| ID | Task | Owner | Branch | Done when |
|---|---|---|---|---|
| T6.1 | Streamlit replay dashboard | S | `feat/T6.1-streamlit-dashboard` | Four subsystem panels plus coordinator panel |
| T6.2 | Learned stacking coordinator with calibration | A | `feat/T6.2-stacking-coordinator` | Compared against rule-based fusion |
| T6.3 | QLoRA fine-tune of a small explanation model | A | `feat/T6.3-qlora-finetune` | Quality, latency and cost compared with the API model |
| T6.4 | Docker Compose packaging | S | `feat/T6.4-docker-compose` | One command brings up the stack |

---

## Tier 7: Hardening and Final (weeks 27–28)

| ID | Task | Owner | Branch | Done when |
|---|---|---|---|---|
| T7.1 | CI hardening and coverage gates | A | `chore/T7.1-ci-hardening` | Threshold enforced |
| T7.2 | Model cards and ADR index | S | `docs/T7.2-model-cards` | Every shipped model has a card |
| T7.3 | Final report compilation and formatting | S | `docs/T7.3-final-report` | Report compiled with figures |
| T7.4 | Viva rehearsal: cross-explain every component | A+S | `docs/T7.4-viva-prep` | Each member explains the other's modules |

