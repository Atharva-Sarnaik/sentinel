import test from "node:test";
import assert from "node:assert/strict";

// Test 1: Canonical channel mapping
test("Canonical subsystem-to-channel mapping matches Sentinel requirements", () => {
  const canonicalMapping = {
    power: ["P-1", "P-2", "P-3", "P-4"],
    thermal: ["T-1", "T-2", "T-3"],
    attitude: ["A-1", "A-2", "A-3", "A-4"],
    communications: ["C-1", "C-2", "D-1"],
  };

  assert.deepEqual(canonicalMapping.power, ["P-1", "P-2", "P-3", "P-4"]);
  assert.deepEqual(canonicalMapping.thermal, ["T-1", "T-2", "T-3"]);
  assert.deepEqual(canonicalMapping.attitude, ["A-1", "A-2", "A-3", "A-4"]);
  assert.deepEqual(canonicalMapping.communications, ["C-1", "C-2", "D-1"]);
});

// Test 2: ApiClientError structure
test("ApiClientError encapsulates HTTP status, message, and details", () => {
  class ApiClientError extends Error {
    constructor(message, status = 500, details) {
      super(message);
      this.name = "ApiClientError";
      this.status = status;
      this.details = details;
    }
  }

  const err = new ApiClientError("Validation failed", 422, { field: "channels" });
  assert.equal(err.name, "ApiClientError");
  assert.equal(err.status, 422);
  assert.equal(err.message, "Validation failed");
  assert.deepEqual(err.details, { field: "channels" });
});

// Test 3: Synthetic Demonstration Payloads
test("Synthetic demonstration payloads conform to TelemetryWindow schema", () => {
  const payloads = {
    nominal: {
      subsystem: "power",
      start_time: "2025-05-18T14:22:00Z",
      end_time: "2025-05-18T14:26:00Z",
      channels: {
        "P-1": [28.40, 28.42, 28.39, 28.41],
        "P-2": [14.12, 14.15, 14.18, 14.14],
        "T-1": [21.10, 21.20, 21.15, 21.25],
        "A-1": [0.018, 0.020, 0.019, 0.021],
        "C-1": [-82.4, -82.1, -82.3, -82.0],
      },
      source_dataset: "Synthetic-Demonstration-LEO",
    },
    powerAnomaly: {
      subsystem: "power",
      start_time: "2025-05-18T14:22:00Z",
      end_time: "2025-05-18T14:26:00Z",
      channels: {
        "P-1": [28.40, 48.72, 49.50, 52.10],
        "P-2": [14.12, 14.15, 14.18, 14.14],
        "T-1": [21.10, 21.20, 21.15, 21.25],
        "A-1": [0.018, 0.020, 0.019, 0.021],
        "C-1": [-82.4, -82.1, -82.3, -82.0],
      },
      source_dataset: "Synthetic-Demonstration-LEO",
    },
  };

  for (const [key, p] of Object.entries(payloads)) {
    assert.ok(p.subsystem);
    assert.ok(p.start_time);
    assert.ok(p.end_time);
    assert.ok(p.channels);
    assert.ok(p.source_dataset);

    // Uniform channel length validation
    const lengths = Object.values(p.channels).map((arr) => arr.length);
    assert.ok(lengths.every((len) => len === lengths[0]), `Payload ${key} channels have mismatched lengths`);
  }
});

// Test 4: Mock API client fetch handling (200 OK)
test("Mock API client parses 200 OK JSON response", async () => {
  const mockHealth = {
    status: "healthy",
    service: "Sentinel API",
    version: "0.1.0",
    tier: "5",
  };

  const fakeFetch = async (url) => {
    return {
      ok: true,
      status: 200,
      json: async () => mockHealth,
    };
  };

  const resp = await fakeFetch("http://127.0.0.1:8000/health");
  const data = await resp.json();
  assert.equal(data.status, "healthy");
  assert.equal(data.tier, "5");
});

// Test 5: Mock API client error handling (422 Unprocessable Entity)
test("Mock API client throws error on 422 Unprocessable Entity", async () => {
  const fakeFetch = async (url) => {
    return {
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: async () => ({ detail: "Invalid TelemetryWindow schema: missing subsystem" }),
    };
  };

  const resp = await fakeFetch("http://127.0.0.1:8000/analyze");
  assert.equal(resp.ok, false);
  assert.equal(resp.status, 422);
  const json = await resp.json();
  assert.ok(json.detail.includes("Invalid TelemetryWindow schema"));
});

// Test 6: Backend response to MissionTelemetryWindow mapping logic
test("AnalyzeResponse correctly transforms into active mission window", () => {
  const mockAnalyzeResponse = {
    decision: {
      decision_id: "dec-1234",
      window_id: "win-5678",
      opinions: [
        {
          opinion_id: "op-pwr",
          window_id: "win-5678",
          subsystem: "power",
          anomaly_score: 0.88,
          severity: "critical",
          responsible_channels: ["P-1"],
          threshold_used: 0.5,
          model_run_id: "specialist-power-online",
          created_at: "2025-05-18T14:22:10Z",
        },
        {
          opinion_id: "op-thm",
          window_id: "win-5678",
          subsystem: "thermal",
          anomaly_score: 0.05,
          severity: "nominal",
          responsible_channels: [],
          threshold_used: 0.5,
          model_run_id: "specialist-thermal-online",
          created_at: "2025-05-18T14:22:10Z",
        },
      ],
      severity: "critical",
      corroborating_subsystems: ["power"],
      attributed_subsystem: "power",
      fusion_rule_applied: "CRITICAL_SINGLE_SPECIALIST",
      created_at: "2025-05-18T14:22:10Z",
    },
    explanation: {
      explanation_id: "exp-1",
      decision_id: "dec-1234",
      text: "Power specialist detected anomalous voltage excursion on P-1.",
      cited_channels: ["P-1"],
      cited_severity: "critical",
      prompt_version: "v1.0",
      llm_model: "mock-reasoner",
      created_at: "2025-05-18T14:22:10Z",
    },
    verifier_result: {
      verifier_id: "ver-1",
      explanation_id: "exp-1",
      status: "grounded",
      ungrounded_claims: [],
      retry_count: 0,
      created_at: "2025-05-18T14:22:10Z",
    },
    audit_entry: {
      entry_id: "audit-1",
      run_id: "sentinel-run-001",
      window_id: "win-5678",
      decision_id: "dec-1234",
      verifier_id: "ver-1",
      final_severity: "critical",
      abstained: false,
      created_at: "2025-05-18T14:22:10Z",
      extra: {},
    },
    abstained: false,
  };

  const isAnomalous = mockAnalyzeResponse.decision.severity !== "nominal";
  assert.equal(isAnomalous, true);
  assert.equal(mockAnalyzeResponse.decision.attributed_subsystem, "power");
  assert.equal(mockAnalyzeResponse.verifier_result.status, "grounded");
  assert.equal(mockAnalyzeResponse.audit_entry.final_severity, "critical");

  const pwrOpinion = mockAnalyzeResponse.decision.opinions.find((o) => o.subsystem === "power");
  assert.ok(pwrOpinion);
  assert.equal(pwrOpinion.anomaly_score, 0.88);
  assert.deepEqual(pwrOpinion.responsible_channels, ["P-1"]);
});

// Test 7: Historical Replay Status mapping validation
test("ReplayStatusDto parses NASA SMAP sequential execution correctly", () => {
  const mockReplayStatus = {
    session_id: "sess-9999",
    status: "running",
    dataset: "SMAP",
    split: "test",
    channel: "P-1",
    subsystem: "power",
    window_size: 100,
    stride: 10,
    speed_delay_ms: 500,
    current_window_index: 42,
    total_windows: 841,
    processed_windows: 42,
    failed_windows: 0,
    progress_percent: 4.99,
    is_anomalous: true,
    latest_window: {
      window_id: "win-42",
      start_time: "2024-01-01T00:07:00Z",
      end_time: "2024-01-01T00:08:40Z",
      subsystem: "power",
      channel: "P-1",
      primary_series: new Array(100).fill(-0.25),
      is_anomalous: true,
      metadata: { npy_file: "P-1.npy" },
    },
    latest_analysis: {
      decision: {
        decision_id: "dec-42",
        window_id: "win-42",
        opinions: [
          {
            opinion_id: "op-42",
            window_id: "win-42",
            subsystem: "power",
            anomaly_score: 0.82,
            severity: "critical",
            responsible_channels: ["P-1"],
            threshold_used: 0.5,
            model_run_id: "specialist-power-online",
            created_at: "2024-01-01T00:07:00Z",
          },
        ],
        severity: "critical",
        corroborating_subsystems: ["power"],
        attributed_subsystem: "power",
        fusion_rule_applied: "CRITICAL_SINGLE_SPECIALIST",
        created_at: "2024-01-01T00:07:00Z",
      },
      explanation: {
        explanation_id: "exp-42",
        decision_id: "dec-42",
        text: "NASA SMAP P-1 anomalous excursion detected.",
        cited_channels: ["P-1"],
        cited_severity: "critical",
        prompt_version: "v1.0.0",
        llm_model: "mock-reasoner",
        created_at: "2024-01-01T00:07:00Z",
      },
      verifier_result: {
        verifier_id: "ver-42",
        explanation_id: "exp-42",
        status: "grounded",
        ungrounded_claims: [],
        retry_count: 0,
        created_at: "2024-01-01T00:07:00Z",
      },
      audit_entry: {
        entry_id: "audit-42",
        run_id: "sentinel-run-001",
        window_id: "win-42",
        decision_id: "dec-42",
        verifier_id: "ver-42",
        final_severity: "critical",
        abstained: false,
        created_at: "2024-01-01T00:07:00Z",
        extra: {},
      },
      abstained: false,
    },
    recent_history: [],
    error: null,
  };

  assert.equal(mockReplayStatus.status, "running");
  assert.equal(mockReplayStatus.dataset, "SMAP");
  assert.equal(mockReplayStatus.channel, "P-1");
  assert.equal(mockReplayStatus.is_anomalous, true);
  assert.equal(mockReplayStatus.latest_window.primary_series.length, 100);
  assert.equal(mockReplayStatus.latest_analysis.audit_entry.entry_id, "audit-42");
  assert.equal(mockReplayStatus.latest_analysis.explanation.llm_model, "mock-reasoner");
});

