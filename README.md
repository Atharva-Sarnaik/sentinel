# 🛰 Sentinel

**Multi-Agent AI System for Satellite Telemetry Health Monitoring and Anomaly Detection**

> Decision-support research prototype, not flight software.

**Status: scaffolding, implementation not started.**
![CI](https://github.com/Atharva-Sarnaik/sentinel/actions/workflows/ci.yml/badge.svg?branch=develop)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Team

| Member | GitHub | Role |
|---|---|---|
| Atharva Sarnaik | [@Atharva-Sarnaik](https://github.com/Atharva-Sarnaik) | Fusion engine, Orchestration, Evaluation, CI |
| Sujal Hede | [@Sujalhede](https://github.com/Sujalhede) | Data plane, Feature plane, Specialists, API |

> For a detailed tier-by-tier breakdown of each member's responsibilities, deliverables, and viva questions, see [`docs/roles_distribution.md`](docs/roles_distribution.md).

**Guide:** Dr. M. S. Arade, Dept. of AI & Data Science, GCE Kolhapur (BE 2026–2027)

---

## Architecture Overview

Data flows bottom-up through five planes. See [`docs/guides/architecture.md`](docs/guides/architecture.md) for the ASCII diagram.

```
Telemetry source (SMAP / MSL replay; ESA-ADB / OPS-SAT as fallback)
  → data-integrity gate  (schema · range · staleness)
  → windowing & feature store  (Parquet + DuckDB · chronological split)
  → four specialist agents  (Power · Thermal · Attitude · Communications)
      each: LSTM Autoencoder + nonparametric dynamic thresholding
      each emits: SpecialistOpinion
  → coordinator
      deterministic fusion engine   → FusionDecision  (sets severity)
      LLM reasoner                  → Explanation     (explains only)
      verifier                      → VerifierResult  (grounding check · retry × 2 · abstain)
      audit log                     → AuditEntry      (written before outcome joined)
  → interfaces: CLI (Typer + Rich) · FastAPI · Streamlit dashboard (Tier 6)
```

**Orchestration:** LangGraph state graph — specialists run in parallel, then join → fuse → reason → verify → audit → emit.

**Cross-cutting:** MLflow + DVC · Langfuse tracing · pytest (incl. leakage regression) · GitHub Actions CI.

---

## Quickstart

### Linux / macOS

```bash
git clone https://github.com/Atharva-Sarnaik/sentinel
cd sentinel
python3.11 -m venv .venv && source .venv/bin/activate
make setup    # installs dev dependencies + pre-commit hooks
make check    # ruff · mypy · import-linter · pytest
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Atharva-Sarnaik/sentinel
cd sentinel
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
.\check.ps1   # ruff · mypy · import-linter · pytest
```

> **Note:** Data files are DVC-tracked and gitignored. See [`data/README.md`](data/README.md) for fetch instructions.

---

## Repository Structure

```
sentinel/
├── apps/
│   ├── cli/                    # Typer + Rich entry point (sentinel CLI)
│   └── dashboard/              # Streamlit replay viewer (Tier 6)
├── services/                   # one folder per component, each with README.md
│   ├── data_plane/             # telemetry adapters, replay, integrity gate
│   ├── feature_plane/          # windowing, normalisation, features, splits
│   ├── specialists/            # shared LSTM-AE template + per-subsystem configs
│   ├── baselines/              # arms A (static threshold), B (Isolation Forest), C (combined LSTM-AE)
│   ├── fusion/                 # deterministic fusion engine + corroboration rules
│   ├── reasoner/               # LLM reasoner, prompt library, output schema
│   ├── verifier/               # grounding check, retry policy, abstention
│   ├── orchestrator/           # LangGraph state graph
│   ├── evaluation/             # metrics, ablation harness (arms A–E), golden set
│   ├── audit/                  # audit log writer
│   ├── api/                    # FastAPI service
│   └── observability/          # Langfuse tracing, cost and latency logging
├── libs/
│   ├── contracts/              # frozen Pydantic v2 models shared by all services
│   ├── config/                 # YAML config (channel→subsystem map, thresholds) + loader
│   └── common/                 # window/time helpers, model registry helpers
├── tests/
│   ├── unit/                   # unit tests (contracts, metrics, fusion rules)
│   ├── integration/            # end-to-end pipeline tests
│   └── leakage/                # permanent leakage regression suite (T0.10)
├── data/                       # gitignored; DVC-tracked; see data/README.md
├── infra/                      # docker-compose (Tier 6), CI helper scripts
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   ├── guides/                 # architecture diagram, how-to guides
│   ├── model_cards/            # one card per shipped model (Tier 7)
│   ├── report/                 # final report (Tier 7)
│   ├── TASKS.md                # full task table with branch names
│   ├── TIERS.md                # tier exit criteria
│   └── HYPOTHESES.md           # H1–H5 tracking (all untested)
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI
│   ├── CODEOWNERS              # per-task ownership
│   └── pull_request_template.md
├── Makefile                    # setup · check · test · lint · format
├── check.ps1                   # Windows PowerShell equivalent of make check
├── pyproject.toml              # single source of truth for project identity and tooling
├── .pre-commit-config.yaml
├── .gitignore
├── LICENSE                     # MIT
├── CONTRIBUTING.md
└── README.md
```

> **Single-change rename:** To rename the project, edit only `pyproject.toml → [project] name`. Everything else references this via the config loader.

---

## Design Rules

The following rules are non-negotiable. They are enforced by import-linter, unit tests, and CI. See [ADR-0002](docs/adr/ADR-0002-design-rules.md) for the full rationale.

| Rule | Statement |
|---|---|
| **LLM role boundary** | The LLM never decides severity or alert level. The fusion engine decides; the LLM only explains. |
| **Verifier grounding** | The verifier rejects any explanation citing a channel, value or severity not present in the evidence object. |
| **Chronological splits** | No random shuffling across the train/test boundary. Splits are strictly chronological. |
| **Headline metrics** | Event-wise precision/recall/F1, detection latency, subsystem attribution accuracy, ungrounded-statement rate. Point-adjusted scores are labelled comparisons only. |
| **Evaluation arms** | Five arms always compared: A static threshold · B Isolation Forest · C single combined LSTM-AE · D specialists alone · E full coordinated system. |
| **Hypotheses** | H1–H5 tracked in `docs/HYPOTHESES.md` as `untested` until real runs exist. |
| **Audit before action** | Every decision is logged to the audit log before any downstream outcome is joined. |

---

## Branching Model and Daily Workflow

See [ADR-0003](docs/adr/ADR-0003-branching.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

| Branch | Purpose |
|---|---|
| `main` | Tier releases only; tagged `tier-N-done`; no direct commits |
| `develop` | Integration; always green; all task branches start here |
| `<type>/<task-id>-<slug>` | Short-lived task branches |

**Daily flow:**
```bash
git switch develop && git pull
git switch -c feat/T1.3-lstm-ae-template
# ... implement ...
make check        # or .\check.ps1
# Open PR → develop (1 approval + green CI → squash-merge → delete branch)
```

**Tier releases:** `develop → main` PR only when tier exit criteria in `docs/TIERS.md` all pass.

---

## Tier and Task Branch Directory

> Full tables with branch names and done-when criteria: [`docs/TASKS.md`](docs/TASKS.md) | Tier exit criteria: [`docs/TIERS.md`](docs/TIERS.md)

**Owner key: A** = Atharva Sarnaik · **S** = Sujal Hede

### Tier 0: Foundations (weeks 1–6, `tier-0-done`) — COMPLETED ✅

| ID | Task | Owner | Status | Done when |
|---|---|---|---|---|
| T0.1 | Dev environment, Makefile/PowerShell, README | S | Done | Fresh clone → green checks on both machines |
| T0.2 | Branch protection, CODEOWNERS, CI green | A | Done | Rules active; CI green on empty repo |
| T0.3 | Contracts library: typed models and tests | A | Done | Contracts frozen and unit-tested |
| T0.4 | Config schema incl. channel→subsystem map | S | Done | YAML + validating loader |
| T0.5 | SMAP/MSL feasibility spike (risk R1) | S | Done | Notebook documents whether a defensible 4-subsystem grouping exists |
| T0.6 | ADR-0001 dataset decision | A | Done | ADR merged after review |
| T0.7 | Telemetry adapter and replay source | S | Done | Windows streamed in time order, no future data |
| T0.8 | Data-integrity gate | A | Done | Stale or corrupt input rejected with reasons |
| T0.9 | Windowing and chronological split | S | Done | Split reproducible; boundary test passes |
| T0.10 | Permanent leakage-regression suite | A | Done | Planted look-ahead bug caught by CI |

### Tier 1: Specialists and Baselines (weeks 7–11, `tier-1-done`) — COMPLETED ✅

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

### Tier 2: Fusion Engine (weeks 12–14, `tier-2-done`) — COMPLETED ✅

| ID | Task | Owner | Status | Done when |
|---|---|---|---|---|
| T2.1 | Severity weighting | A | Done | Deterministic, documented, unit-tested |
| T2.2 | Cross-subsystem corroboration rules | A | Done | Rules in config, golden-case tests |
| T2.3 | Subsystem attribution logic | S | Done | Attribution output matches contract |
| T2.4 | Fusion golden cases and property tests | S | Done | Same input always gives same decision |

### Tier 3: Orchestration, Reasoner, Verifier, Audit (weeks 15–17, `tier-3-done`)

| ID | Task | Owner | Done when |
|---|---|---|---|
| T3.1 | LangGraph skeleton with mock LLM | A | Graph runs end-to-end offline |
| T3.2 | LLM reasoner, prompt library, JSON schema | A | Prompts versioned in files; schema-valid output |
| T3.3 | Verifier grounding check | S | Ungrounded claim flagged via `VerifierResult` |
| T3.4 | Retry policy and abstention path | A | Max 2 retries, then evidence-only report |
| T3.5 | Audit log | S | Every decision logged before any outcome is joined |
| T3.6 | Tracing, cost and latency logging (Langfuse) | A | Each LLM call traced |

### Tier 4: Evaluation and Ablation (weeks 18–20, `tier-4-done`)

| ID | Task | Owner | Done when |
|---|---|---|---|
| T4.1 | Event-wise metrics, latency, attribution accuracy | A | Metrics unit-tested on synthetic cases |
| T4.2 | Ablation harness (arms A–E) | A | One command runs all arms on identical windows |
| T4.3 | Golden set for explanation grounding | S | Labelled set committed |
| T4.4 | Run experiments, results tables | S | Tables with run IDs and raw metrics |
| T4.5 | H1–H5 verdicts, negative results included | A | `docs/HYPOTHESES.md` updated from real runs |

### Tier 5: Interfaces (weeks 21–22, `tier-5-done`)

| ID | Task | Owner | Done when |
|---|---|---|---|
| T5.1 | CLI commands (`analyze`, `evaluate`, `report`) | A | Documented with examples |
| T5.2 | FastAPI service | S | Typed endpoints, tests |
| T5.3 | HTML/JSON report export | S | `analyze --report html` works |
| T5.4 | CLI polish and one-command demo script | A | Demo runs from a clean clone |

### Tier 6: Extended Objectives (weeks 23–26, `tier-6-done`) — only if Tier 4 results exist

| ID | Task | Owner | Done when |
|---|---|---|---|
| T6.1 | Streamlit replay dashboard | S | Four subsystem panels plus coordinator panel |
| T6.2 | Learned stacking coordinator with calibration | A | Compared against rule-based fusion |
| T6.3 | QLoRA fine-tune of a small explanation model | A | Quality, latency and cost compared with the API model |
| T6.4 | Docker Compose packaging | S | One command brings up the stack |

### Tier 7: Hardening and Final (weeks 27–28, `tier-7-done`)

| ID | Task | Owner | Done when |
|---|---|---|---|
| T7.1 | CI hardening and coverage gates | A | Threshold enforced |
| T7.2 | Model cards and ADR index | S | Every shipped model has a card |
| T7.3 | Final report compilation and formatting | S | Report compiled with figures |
| T7.4 | Viva rehearsal: cross-explain every component | A+S | Each member explains the other's modules |

---

## Evaluation Protocol and Hypotheses

### Evaluation Arms

| Arm | System | Purpose |
|---|---|---|
| A | Static threshold | Simplest baseline |
| B | Isolation Forest | Classical ML baseline |
| C | Single combined LSTM-AE | Deep learning baseline |
| D | Four specialists (no coordinator) | Ablate coordinator value |
| E | Full Sentinel (specialists + fusion + LLM) | Proposed system |

Arms A–E always run on **identical** windows (task T4.2).

### Hypotheses (all `untested`)

| ID | Statement |
|---|---|
| H1 | Full system (arm E) > best single-model baseline on event-wise F1 |
| H2 | Cross-subsystem corroboration (arm E) reduces false positives vs specialists alone (arm D) |
| H3 | Verifier accepts ≥ 90% of explanations on first attempt |
| H4 | Each specialist LSTM-AE outperforms the combined model (arm C) for its own subsystem |
| H5 | Dynamic thresholding achieves lower FPR than static thresholds (arm A) at equal recall |

Full tracking in [`docs/HYPOTHESES.md`](docs/HYPOTHESES.md). Negative results will be reported.

---

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | SMAP/MSL channel-to-subsystem grouping is unverified | Task T0.5 (feasibility spike); ADR-0001 records the decision; fallback to ESA-ADB/OPS-SAT |
| R2 | LLM API cost on RTX 4050 / laptop budget | Use `gpt-4o-mini`; Langfuse cost tracking (T3.6); QLoRA fallback (T6.3) |
| R3 | Annotation availability for event-wise evaluation | SMAP/MSL provide point labels; event construction methodology documented in T4.1 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Data contracts | Pydantic v2 |
| Feature store | Parquet + DuckDB |
| Deep learning | PyTorch |
| ML baselines | scikit-learn |
| Orchestration | LangGraph |
| LLM | OpenAI API (gpt-4o-mini); QLoRA fine-tune (T6.3) |
| Experiment tracking | MLflow + DVC |
| Tracing | Langfuse |
| CLI | Typer + Rich |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit (Tier 6) |
| Audit store | SQLite (dev) / PostgreSQL (prod) |
| CI | GitHub Actions |
| Linting | Ruff |
| Type checking | Mypy (strict on `libs/`) |
| Import safety | import-linter |
| Pre-commit | pre-commit |

---

## Read Next

- [CONTRIBUTING.md](CONTRIBUTING.md) — environment setup, daily workflow, code standards
- [docs/roles_distribution.md](docs/roles_distribution.md) — complete tier-by-tier role breakdown and viva defense guide
- [docs/TIERS.md](docs/TIERS.md) — tier exit criteria
- [docs/TASKS.md](docs/TASKS.md) — full task table with branch names
- [docs/HYPOTHESES.md](docs/HYPOTHESES.md) — H1–H5 tracking
- [docs/adr/ADR-0001-dataset-decision.md](docs/adr/ADR-0001-dataset-decision.md) — dataset decision (pending T0.5)
- [docs/adr/ADR-0002-design-rules.md](docs/adr/ADR-0002-design-rules.md) — non-negotiable design rules
- [docs/adr/ADR-0003-branching.md](docs/adr/ADR-0003-branching.md) — branching model

---

## License

MIT — see [LICENSE](LICENSE).

