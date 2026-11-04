## Pull Request Checklist

Before requesting review, confirm all items below:

### Traceability
- [ ] This PR is linked to a task ID from `docs/TASKS.md` (e.g. `Closes T1.3`).
- [ ] The branch name follows the convention `<type>/<task-id>-<slug>` (e.g. `feat/T1.3-lstm-ae-template`).

### Tests
- [ ] New tests added (or existing tests updated) for every changed behaviour.
- [ ] `make check` / `.\check.ps1` passes locally (ruff + mypy + import-linter + pytest).
- [ ] Leakage regression suite (`pytest tests/leakage`) is green.

### Results integrity
- [ ] **No accuracy, F1, or any experimental result is claimed without a valid MLflow/DVC run ID.**
- [ ] If a hypothesis status changed in `docs/HYPOTHESES.md`, the run ID is cited inline.

### Design rules (ADR-0002)
- [ ] The LLM does not decide severity or alert level (fusion engine only).
- [ ] No test timestamp appears before the latest train timestamp (chronological split).
- [ ] AuditEntry is written before any downstream outcome is joined.

### Review
- [ ] Cross-reviewed by the other teammate (both members can explain this component in the viva).
- [ ] CI is green.

---

**Task ID:** <!-- e.g. T1.3 -->
**Description:** <!-- brief description of what this PR does -->

