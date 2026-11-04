# Architecture Overview

> **Status:** diagram placeholder — will be filled during task T0.1.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SENTINEL PIPELINE                           │
│              (decision-support prototype, not flight software)      │
└─────────────────────────────────────────────────────────────────────┘

  Telemetry Source (SMAP / MSL / ESA-ADB / OPS-SAT replay)
       │
       ▼
  ┌─────────────┐
  │  data_plane │  ← integrity gate (schema, range, staleness)
  └──────┬──────┘
         │  TelemetryWindow
         ▼
  ┌──────────────┐
  │ feature_plane│  ← windowing, normalisation, chronological split
  └──────┬───────┘
         │  Normalised TelemetryWindow
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │                   SPECIALISTS (parallel)                 │
  │   ┌───────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐   │
  │   │ Power │  │ Thermal │  │ Attitude │  │  Comms   │   │
  │   │LSTM-AE│  │ LSTM-AE │  │ LSTM-AE  │  │ LSTM-AE  │   │
  │   └───┬───┘  └────┬────┘  └────┬─────┘  └────┬─────┘   │
  └───────┼───────────┼────────────┼──────────────┼─────────┘
          │           │            │              │
          └───────────┴────────────┴──────────────┘
                              │  List[SpecialistOpinion]
                              ▼
                    ┌─────────────────┐
                    │  fusion engine  │  ← deterministic; sets severity
                    └────────┬────────┘
                             │  FusionDecision
                             ▼
                    ┌─────────────────┐
                    │  LLM reasoner   │  ← explains only; never decides
                    └────────┬────────┘
                             │  Explanation
                             ▼
                    ┌─────────────────┐
                    │    verifier     │  ← grounding check; retry × 2
                    └────────┬────────┘
                             │  VerifierResult
                        ┌────┴────┐
                     grounded  ungrounded (abstain after 2 retries)
                        │
                        ▼
                    ┌─────────────────┐
                    │   audit log     │  ← written before outcome joined
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  CLI / API /    │
                    │  Dashboard      │
                    └─────────────────┘

Cross-cutting: MLflow + DVC, Langfuse tracing, pytest CI
```

