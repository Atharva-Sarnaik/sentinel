# Tier Directory

> See `docs/TASKS.md` for the full task table with branch names and done-when criteria.

---

## Tier 0: Foundations — weeks 1–6 — `tier-0-done` ✅

**Status:** Completed
**Exit criteria:** Fresh clone → green checks on both machines; SMAP/MSL feasibility verdict recorded (ADR-0001 accepted); adapter streams windows in time order; leakage suite catches planted bug and production split passes with zero leakage. All 40 unit and leakage tests pass.

---

## Tier 1: Specialists and Baselines — weeks 7–11 — `tier-1-done`

**Exit criteria:** All three baselines run in harness; four specialists trained; per-subsystem metrics table with MLflow run IDs exists; `sentinel specialists-report` command works.

---

## Tier 2: Fusion Engine — weeks 12–14 — `tier-2-done`

**Exit criteria:** Fusion engine is deterministic, unit-tested; corroboration rules pass golden cases; attribution output matches contract.

---

## Tier 3: Orchestration, Reasoner, Verifier, Audit — weeks 15–17 — `tier-3-done`

**Exit criteria:** LangGraph graph runs end-to-end offline; LLM reasoner produces schema-valid output with versioned prompts; verifier flags ungrounded claims; retry/abstention path tested; audit log written before outcomes; every LLM call traced in Langfuse.

---

## Tier 4: Evaluation and Ablation — weeks 18–20 — `tier-4-done`

**Exit criteria:** Metrics unit-tested on synthetic cases; one command runs all five arms; golden set committed; results tables with run IDs exist; H1–H5 verdicts updated from real runs (negative results included).

---

## Tier 5: Interfaces — weeks 21–22 — `tier-5-done`

**Exit criteria:** CLI commands (`analyze`, `evaluate`, `report`) documented with examples; FastAPI endpoints typed and tested; HTML/JSON export works; one-command demo runs from clean clone.

---

## Tier 6: Extended Objectives — weeks 23–26 — `tier-6-done`

> **Only started if Tier 4 results exist.**

**Exit criteria:** Streamlit dashboard shows four subsystem panels + coordinator panel; learned stacking coordinator compared against rule-based fusion; QLoRA fine-tune compared with API model; Docker Compose brings up the full stack.

---

## Tier 7: Hardening and Final — weeks 27–28 — `tier-7-done`

**Exit criteria:** CI coverage gates enforced; every shipped model has a model card; ADR index complete; final report compiled; both members can explain the other's modules in viva rehearsal.

