# Sentinel FastAPI Web Service Guide

**Version:** 0.1.0  
**Entry Point:** `services.api.app:app`

---

## 1. Overview

Sentinel provides a high-performance RESTful API built on [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/) for real-time telemetry streaming, multi-agent health analysis, run manifest retrieval, and immutable audit inspection.

```powershell
# Start local API development server
uvicorn services.api.app:app --reload --port 8000
```

The interactive OpenAPI documentation is automatically served at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 2. API Endpoints

### 2.1 Health Check (`GET /health`)

Verifies service availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "Sentinel API",
  "version": "0.1.0",
  "tier": "5"
}
```

---

### 2.2 Telemetry Analysis (`POST /analyze`)

Submits a validated `TelemetryWindow` for full multi-agent processing.

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "subsystem": "power",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-01T00:04:00Z",
    "channels": {
      "P-1": [28.0, 28.1, 48.5, 49.0],
      "T-1": [45.0, 45.2, 72.0, 75.0],
      "A-1": [1.0, 1.0, 1.0, 1.0],
      "C-1": [5.0, 5.0, 5.0, 5.0]
    },
    "source_dataset": "Live-Replay"
  }'
```

**Response (200 OK):**
```json
{
  "decision": {
    "decision_id": "8a32bb58-1f59-43c7-9759-4c92a95df6bd",
    "window_id": "4b68e987-a2e6-44d0-8f6f-bd74d801b06a",
    "severity": "critical",
    "attributed_subsystem": "power",
    "fusion_rule_applied": "power_thermal_coupling",
    "corroborating_subsystems": ["power", "thermal"],
    "opinions": [
      {
        "subsystem": "power",
        "anomaly_score": 0.85,
        "severity": "critical",
        "responsible_channels": ["P-1"],
        "threshold_used": 0.5
      },
      {
        "subsystem": "thermal",
        "anomaly_score": 0.85,
        "severity": "critical",
        "responsible_channels": ["T-1"],
        "threshold_used": 0.5
      }
    ]
  },
  "explanation": {
    "text": "Subsystem 'power' flagged an anomaly with severity critical. Telemetry evidence observed on channel(s): P-1, T-1. Fusion rule 'power_thermal_coupling' applied."
  },
  "verifier_result": {
    "status": "grounded",
    "is_grounded": true,
    "retry_count": 0
  },
  "audit_entry": {
    "entry_id": "9b12cc87-b2e6-44d0-8f6f-bd74d801b06a",
    "final_severity": "critical",
    "abstained": false
  },
  "abstained": false
}
```

---

### 2.3 List Runs (`GET /runs`)

Retrieves all recorded experiment run manifests from `artifacts/runs/`.

**Response (200 OK):**
```json
[
  {
    "run_id": "exp-arm-e-sentinel-42",
    "description": "Arm E Full Coordinated Multi-Agent Sentinel evaluation run",
    "created_at": "2026-11-16T10:17:46.537549Z",
    "dataset_dvc_hash": "05435ac72338...",
    "config_hash": "1b1884c2dd23..."
  }
]
```

---

### 2.4 Get Run Manifest & Metrics (`GET /runs/{run_id}`)

Retrieves a specific run manifest and its metrics dictionary.

**Request:**
```bash
curl -X GET "http://localhost:8000/runs/exp-arm-e-sentinel-42"
```

**Response (200 OK):**
```json
{
  "manifest": {
    "run_id": "exp-arm-e-sentinel-42",
    "description": "Arm E Full Coordinated Multi-Agent Sentinel evaluation run",
    "git_commit": "d5ea6967530d..."
  },
  "metrics": {
    "precision": 0.3333,
    "recall": 1.0,
    "f1": 0.5,
    "false_positive_rate": 1.0,
    "event_f1": 1.0,
    "detection_latency": 0.0
  }
}
```

---

### 2.5 Get Audit Entry (`GET /audit/{entry_id}`)

Retrieves an immutable audit log entry by UUID.

**Request:**
```bash
curl -X GET "http://localhost:8000/audit/9b12cc87-b2e6-44d0-8f6f-bd74d801b06a"
```
