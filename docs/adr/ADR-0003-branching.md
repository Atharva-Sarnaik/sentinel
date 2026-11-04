# ADR-0003: Branching Model

**Status:** `accepted`

**Date:** 2026-11-04

**Authors:** Atharva Sarnaik (`@Atharva-Sarnaik`), Sujal Hede (`@Sujalhede`)

---

## Context

A two-person team needs a lightweight but disciplined branching strategy that:
- Keeps `main` always deployable and tagged at tier boundaries.
- Prevents untested code from reaching `main`.
- Makes every component reviewable by the cross-teammate (viva requirement).
- Works with GitHub Actions CI and branch protection rules.

---

## Decision

### Branch Hierarchy

```
main            ← tier releases only; tagged tier-N-done; no direct commits
  └── develop   ← integration branch; always green; PR target for all work
        └── <type>/<task-id>-<slug>   ← short-lived task branches
```

### Branch Types

| Prefix | Use |
|---|---|
| `feat/` | New feature implementation |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `chore/` | Tooling, config, CI |
| `exp/` | Experiments (may not merge) |

### Branch Naming

`<type>/<task-id>-<slug>` — e.g. `feat/T1.3-lstm-ae-template`, `docs/T0.1-readme`.

### Daily Workflow

```bash
git switch develop && git pull
git switch -c feat/T1.3-lstm-ae-template
# ... implement, commit ...
.\check.ps1   # Windows
make check    # Linux/macOS
# Open PR → develop (1 approval from the other teammate + green CI)
# Squash-merge → delete branch
```

### Tier Releases

```bash
# When all tier exit criteria in docs/TIERS.md pass:
git switch develop && git pull
# Open PR: develop → main
# Squash-merge after review
git tag tier-N-done
git push origin tier-N-done
```

### Protection Rules

- `main`: no direct pushes; require PR, 1 approval, green CI.
- `develop`: require PR, 1 approval, green CI.
- Both protected via GitHub branch protection rules (task T0.2).

---

## Consequences

- Every task has a cross-review by the other teammate — both members can explain every component in the viva.
- Short-lived branches minimise merge conflicts on a 2-person team.
- `exp/` branches may accumulate; prune regularly.

---

## References

- Task T0.1: dev environment setup
- Task T0.2: branch protection and CODEOWNERS
- `CONTRIBUTING.md`: daily workflow details

