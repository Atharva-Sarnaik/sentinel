# Contributing to Sentinel

> Government College of Engineering, Kolhapur — Dept. of AI & Data Science, BE 2026–2027

**Status:** scaffolding, implementation not started.

---

## Table of Contents

1. [Team](#team)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Daily Workflow](#daily-workflow)
5. [Branching Model](#branching-model)
6. [Code Standards](#code-standards)
7. [Running Checks](#running-checks)
8. [Pull Request Process](#pull-request-process)
9. [Design Rules](#design-rules)

---

## Team

| Member | GitHub | Role |
|---|---|---|
| Atharva Sarnaik | [@Atharva-Sarnaik](https://github.com/Atharva-Sarnaik) | Fusion, Orchestration, Evaluation, CI |
| Sujal Hede | [@Sujalhede](https://github.com/Sujalhede) | Data, Features, Specialists, API |

Guide: **Dr. M. S. Arade**, Dept. of AI & Data Science, GCE Kolhapur.

---

## Prerequisites

- Python 3.11 (use [pyenv](https://github.com/pyenv/pyenv) or the official installer)
- Git ≥ 2.40
- PowerShell 7+ (Windows) or Bash (Linux/macOS)
- A CUDA-capable GPU is optional for local training (the project targets a single RTX 4050)

---

## Environment Setup

### Linux / macOS

```bash
git clone https://github.com/Atharva-Sarnaik/sentinel
cd sentinel
python3.11 -m venv .venv
source .venv/bin/activate
make setup        # pip install -e ".[dev]" + pre-commit install
make check        # verify everything passes
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Atharva-Sarnaik/sentinel
cd sentinel
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
.\check.ps1       # verify everything passes
```

---

## Daily Workflow

```bash
# 1. Sync develop
git switch develop && git pull

# 2. Create a task branch
git switch -c feat/T1.3-lstm-ae-template

# 3. Implement, commit in small logical units
# 4. Run checks before pushing
make check        # Linux/macOS
.\check.ps1       # Windows

# 5. Push and open PR → develop
git push -u origin feat/T1.3-lstm-ae-template
# → GitHub: open PR, fill in the PR checklist
```

**Commit message format:** `<type>(T<id>): <short description>`
Examples:
- `feat(T1.3): add LSTM-AE template skeleton`
- `fix(T0.9): ensure chronological split boundary is inclusive`
- `docs(T0.6): merge ADR-0001 dataset decision`

---

## Branching Model

See [ADR-0003](docs/adr/ADR-0003-branching.md) for the full rationale.

| Branch | Purpose | Protection |
|---|---|---|
| `main` | Tier releases only; tagged `tier-N-done` | No direct pushes; 1 approval + green CI |
| `develop` | Integration; always green | No direct pushes; 1 approval + green CI |
| `feat/<id>-<slug>` | Feature implementation | None (short-lived) |
| `fix/<id>-<slug>` | Bug fixes | None |
| `docs/<id>-<slug>` | Documentation | None |
| `chore/<id>-<slug>` | Tooling, CI, config | None |
| `exp/<id>-<slug>` | Experiments (may not merge) | None |

### Tier releases

```bash
# When all tier exit criteria in docs/TIERS.md pass:
git switch develop && git pull
# Open PR: develop → main (both teammates review)
# Squash-merge, then tag:
git tag tier-N-done
git push origin tier-N-done
```

---

## Code Standards

- **Python 3.11.** Use `from __future__ import annotations` for forward refs.
- **Pathlib everywhere.** No `os.path`; no shell-only string paths.
- **Pydantic v2 for all data contracts.** Models in `libs/contracts/` only.
- **Type hints required** in `libs/`. Relaxed (but encouraged) in `services/` and `apps/`.
- **Stubs raise `NotImplementedError`.** Never claim functionality not yet implemented.
- **Never commit results** without an MLflow/DVC run ID (see ADR-0002).
- **Import linter rules:** services may only import `libs.*`, never each other directly (except the orchestrator).

---

## Running Checks

All checks must pass before opening a PR.

### Linux / macOS

```bash
make format   # ruff format + ruff check --fix
make lint     # ruff check + mypy libs/ + import-linter
make test     # pytest tests/unit tests/leakage
make check    # all of the above
```

### Windows (PowerShell)

```powershell
.\check.ps1              # all checks
.\check.ps1 -SkipTests   # lint only
.\check.ps1 -SkipLint    # tests only
```

### Individual tools

```bash
python -m ruff check .
python -m ruff format .
python -m mypy libs/
python -m importlinter
python -m pytest tests/leakage -v   # leakage suite specifically
```

---

## Pull Request Process

1. Open a PR from your task branch into `develop`.
2. Fill in every checkbox in the [PR template](.github/pull_request_template.md).
3. Assign the other teammate as reviewer.
4. Wait for 1 approval and green CI before merging.
5. Use **squash merge**; delete the branch after merge.
6. Never merge your own PR without the other teammate's approval.

**Key rule:** No result (accuracy, F1, latency) may be claimed in any file without a corresponding MLflow run ID and DVC dataset hash.

---

## Design Rules

The following rules are non-negotiable (see [ADR-0002](docs/adr/ADR-0002-design-rules.md)):

1. **LLM never decides severity** — only the fusion engine does.
2. **Verifier rejects ungrounded claims** — channels/values not in evidence are flagged.
3. **Chronological splits only** — no random shuffling across the train/test boundary.
4. **Headline metrics** — event-wise P/R/F1, detection latency, attribution accuracy, ungrounded-statement rate.
5. **Audit before action** — every decision logged before any downstream outcome is joined.
6. **Hypotheses tracked as `untested`** until real runs exist.

Violations of these rules are grounds for PR rejection.

