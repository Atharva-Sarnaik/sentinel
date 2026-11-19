"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode, useRef } from "react";
import { MissionTelemetryWindow, SeverityType, SubsystemType } from "../types/telemetry";
import { MOCK_WINDOWS } from "../lib/mock-data";
import {
  AnalyzeResponse,
  AuditEntryDto,
  DEMO_TELEMETRY_PAYLOADS,
  HealthResponse,
  ReplayCatalogDto,
  ReplayStatusDto,
  RunDetailsDto,
  RunManifestDto,
  TelemetryWindowRequest,
  analyzeTelemetry,
  getAuditEntry,
  getHealth,
  getReplayCatalog,
  getReplayStatus,
  getRunDetails,
  listRuns,
  pauseReplay,
  resumeReplay,
  startReplay,
  stopReplay,
  updateReplayConfig,
} from "../lib/api";

export type ApiConnectionState = "connected" | "connecting" | "disconnected" | "error";

export interface TelemetryContextType {
  // Navigation & Replay State
  windowIndex: number;
  currentWindow: MissionTelemetryWindow;
  totalWindows: number;
  setWindowIndex: (idx: number) => void;
  nextWindow: () => void;
  prevWindow: () => void;
  exportAuditReport: () => void;

  // Backend Health & Connectivity
  apiStatus: ApiConnectionState;
  apiHealth: HealthResponse | null;
  apiError: string | null;
  refreshHealth: () => Promise<void>;

  // Real-Time Analysis Pipeline Integration (/analyze)
  isAnalyzing: boolean;
  latestBackendResponse: AnalyzeResponse | null;
  lastAnalysisError: string | null;
  runAnalysis: (
    payloadOrScenario?: "nominal" | "powerAnomaly" | "thermalAnomaly" | TelemetryWindowRequest
  ) => Promise<AnalyzeResponse | null>;
  resetToSimulated: () => void;

  // NASA Historical Telemetry Replay (/replay/*)
  replayCatalog: ReplayCatalogDto | null;
  replayStatus: ReplayStatusDto | null;
  selectedDataset: "SMAP" | "MSL";
  selectedSplit: "train" | "test";
  selectedChannel: string;
  replaySpeedMs: number;
  pauseOnAnomaly: boolean;
  isReplaying: boolean;
  replayError: string | null;
  setSelectedDataset: (ds: "SMAP" | "MSL") => void;
  setSelectedSplit: (split: "train" | "test") => void;
  setSelectedChannel: (ch: string) => void;
  setReplaySpeedMs: (ms: number) => void;
  togglePauseOnAnomaly: (enabled: boolean) => Promise<void>;
  startHistoricalReplay: (startWindow?: number, pauseOnAnom?: boolean) => Promise<void>;
  pauseHistoricalReplay: () => Promise<void>;
  resumeHistoricalReplay: () => Promise<void>;
  stopHistoricalReplay: () => Promise<void>;
  refreshReplayCatalog: () => Promise<void>;

  // Run History & Metrics Retrieval (/runs, /runs/{run_id})
  runs: RunManifestDto[];
  activeRunDetails: RunDetailsDto | null;
  isLoadingRuns: boolean;
  refreshRuns: () => Promise<void>;
  selectRun: (runId: string) => Promise<RunDetailsDto | null>;

  // Audit Record Retrieval (/audit/{entry_id})
  fetchAuditById: (entryId: string) => Promise<AuditEntryDto | null>;
}

const TelemetryContext = createContext<TelemetryContextType | undefined>(undefined);

function mapBackendResponseToWindow(
  response: AnalyzeResponse,
  payload: TelemetryWindowRequest,
  baseWindow: MissionTelemetryWindow
): MissionTelemetryWindow {
  const { decision, explanation, verifier_result, audit_entry, abstained } = response;
  const isAnomalous = decision.severity !== "nominal";

  // Build updated subsystems map based on specialist opinions
  const updatedSubsystems = { ...baseWindow.subsystems };

  for (const opinion of decision.opinions) {
    const subKey = opinion.subsystem.toLowerCase() as SubsystemType;
    if (updatedSubsystems[subKey]) {
      const existing = updatedSubsystems[subKey];
      const channels = { ...existing.channels };

      // Update channels provided in the analyzed payload
      for (const [chKey, values] of Object.entries(payload.channels)) {
        const prefix = chKey.split("-")[0].toUpperCase();
        const matchesSubsystem =
          (prefix === "P" && subKey === "power") ||
          (prefix === "T" && subKey === "thermal") ||
          (prefix === "A" && subKey === "attitude") ||
          ((prefix === "C" || prefix === "D") && subKey === "communications");

        if (matchesSubsystem && channels[chKey]) {
          const currentVal = values.length > 0 ? values[values.length - 1] : channels[chKey].currentValue;
          const mean = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : currentVal;
          channels[chKey] = {
            ...channels[chKey],
            currentValue: currentVal,
            mean: parseFloat(mean.toFixed(2)),
            history: values.length > 0 ? values : channels[chKey].history,
            isAnomalous: opinion.responsible_channels.includes(chKey),
          };
        }
      }

      updatedSubsystems[subKey] = {
        ...existing,
        model: opinion.model_run_id,
        anomalyScore: opinion.anomaly_score,
        threshold: opinion.threshold_used,
        severity: opinion.severity as SeverityType,
        responsibleChannels: opinion.responsible_channels,
        channels,
      };
    }
  }

  return {
    ...baseWindow,
    windowId: decision.window_id,
    timestamp: new Date(decision.created_at).toISOString().replace("T", " ").slice(0, 19) + " UTC",
    status: isAnomalous ? "ANOMALOUS" : "NORMAL",
    groundTruth: isAnomalous,
    dataSource: "backend",
    backendRunId: audit_entry.run_id,
    cohesionIndex: isAnomalous ? 74.2 : 99.4,
    bayesianAnomalyProb: isAnomalous ? 0.884 : 0.012,
    activeAnomaliesCount: decision.opinions.filter((o) => o.severity !== "nominal").length,
    groundingVerification: {
      status: verifier_result.status === "grounded" ? "GROUNDED" : "ABSTAINED",
      retries: verifier_result.retry_count,
      latencyMs: 38,
    },
    auditLog: {
      entryId: audit_entry.entry_id,
      decisionId: audit_entry.decision_id,
      hash: `${audit_entry.entry_id.slice(0, 8)}...${audit_entry.entry_id.slice(-5)}`,
      status: "COMMITTED",
      timestamp: audit_entry.created_at,
    },
    fusionDecision: {
      severity: decision.severity as SeverityType,
      corroborationRule: decision.fusion_rule_applied,
      concurrenceRatio: `${decision.corroborating_subsystems.length}/4 SPECIALISTS`,
      attributedSubsystem: decision.attributed_subsystem?.toUpperCase() || "NONE",
      explanationText:
        explanation?.text ||
        (abstained
          ? "Explanation generation was abstained by the grounding verifier due to ungrounded claims."
          : "Autonomous multi-agent synthesis verified zero divergent anomalies across subsystems."),
      citedChannels: explanation?.cited_channels || [],
      citedSeverity: (explanation?.cited_severity || decision.severity) as SeverityType,
      consensusEntropy: isAnomalous ? 0.724 : 0.014,
      reasonerProvider: String(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.provider as string) ||
          audit_entry.extra?.provider ||
          explanation?.llm_model ||
          "openai"
      ),
      reasonerModel: String(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.model as string) ||
          audit_entry.extra?.model ||
          explanation?.llm_model ||
          "gpt-4o-mini"
      ),
      isFallback: Boolean(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.is_fallback as boolean) ??
          audit_entry.extra?.is_fallback ??
          false
      ),
      fallbackReason:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.fallback_reason as string) ||
          (audit_entry.extra?.fallback_reason as string) ||
          null),
      recommendations:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.recommendations as string[]) ||
          (audit_entry.extra?.recommendations as string[]) ||
          []),
      supportingEvidence:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.supporting_evidence as string[]) ||
          (audit_entry.extra?.supporting_evidence as string[]) ||
          []),
      reasonerLatencyMs:
        typeof (audit_entry.extra?.reasoner as Record<string, unknown>)?.latency_ms === "number"
          ? ((audit_entry.extra?.reasoner as Record<string, unknown>).latency_ms as number)
          : typeof audit_entry.extra?.latency_ms === "number"
          ? (audit_entry.extra.latency_ms as number)
          : 38,
    },
    subsystems: updatedSubsystems,
  };
}

function mapReplayStatusToWindow(
  status: ReplayStatusDto,
  baseWindow: MissionTelemetryWindow
): MissionTelemetryWindow | null {
  if (!status.latest_analysis || !status.latest_window) {
    return null;
  }

  const { latest_analysis, latest_window } = status;
  const { decision, explanation, verifier_result, audit_entry, abstained } = latest_analysis;

  const isAnomalous = Boolean(status.is_anomalous) || decision.severity !== "nominal";
  const updatedSubsystems = { ...baseWindow.subsystems };

  for (const opinion of decision.opinions) {
    const subKey = opinion.subsystem.toLowerCase() as SubsystemType;
    if (updatedSubsystems[subKey]) {
      const existing = updatedSubsystems[subKey];
      const channels = { ...existing.channels };

      if (subKey === status.subsystem.toLowerCase()) {
        const series = latest_window.primary_series || [];
        const currentVal = series.length > 0 ? series[series.length - 1] : 0.0;
        const mean = series.length > 0 ? series.reduce((a, b) => a + b, 0) / series.length : currentVal;

        const chKey = status.channel;
        channels[chKey] = {
          id: chKey,
          name: channels[chKey]?.name || `NASA ${status.dataset} Channel ${chKey}`,
          unit: channels[chKey]?.unit || "norm",
          baseline: channels[chKey]?.baseline || "±0.50 norm",
          limit: channels[chKey]?.limit || "±1.00 norm",
          currentValue: parseFloat(currentVal.toFixed(4)),
          mean: parseFloat(mean.toFixed(4)),
          stdDev: 0.12,
          isAnomalous: Boolean(status.is_anomalous),
          history: series.length > 0 ? series : (channels[chKey]?.history || []),
        };
      }

      updatedSubsystems[subKey] = {
        ...existing,
        model: opinion.model_run_id,
        anomalyScore: opinion.anomaly_score,
        threshold: opinion.threshold_used,
        severity: opinion.severity as SeverityType,
        responsibleChannels: opinion.responsible_channels,
        channels,
      };
    }
  }

  return {
    ...baseWindow,
    windowIndex: status.current_window_index,
    windowId: latest_window.window_id,
    timestamp: new Date(latest_window.start_time).toISOString().replace("T", " ").slice(0, 19) + " UTC",
    status: isAnomalous ? "ANOMALOUS" : "NORMAL",
    groundTruth: Boolean(status.is_anomalous),
    dataSource: "backend",
    backendRunId: `NASA-${status.dataset}-${status.split.toUpperCase()}-${status.channel}`,
    cohesionIndex: isAnomalous ? 62.4 : 99.1,
    bayesianAnomalyProb: isAnomalous ? 0.965 : 0.015,
    activeAnomaliesCount: decision.opinions.filter((o) => o.severity !== "nominal").length,
    groundingVerification: {
      status: verifier_result.status === "grounded" ? "GROUNDED" : "ABSTAINED",
      retries: verifier_result.retry_count,
      latencyMs: 28,
    },
    auditLog: {
      entryId: audit_entry.entry_id,
      decisionId: audit_entry.decision_id,
      hash: `${audit_entry.entry_id.slice(0, 8)}...${audit_entry.entry_id.slice(-5)}`,
      status: "COMMITTED",
      timestamp: audit_entry.created_at,
    },
    fusionDecision: {
      severity: decision.severity as SeverityType,
      corroborationRule: decision.fusion_rule_applied,
      concurrenceRatio: `${decision.corroborating_subsystems.length}/4 SPECIALISTS`,
      attributedSubsystem:
        decision.attributed_subsystem?.toUpperCase() || (isAnomalous ? status.subsystem.toUpperCase() : "NONE"),
      explanationText:
        explanation?.text ||
        (abstained
          ? "Explanation generation was abstained by the grounding verifier due to ungrounded claims."
          : `Deterministic fusion synthesis of ${status.dataset} channel ${status.channel}: Subsystem health evaluated under rule '${decision.fusion_rule_applied}'.`),
      citedChannels: explanation?.cited_channels?.length ? explanation.cited_channels : [status.channel],
      citedSeverity: (explanation?.cited_severity || decision.severity) as SeverityType,
      consensusEntropy: isAnomalous ? 0.785 : 0.018,
      reasonerProvider: String(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.provider as string) ||
          audit_entry.extra?.provider ||
          explanation?.llm_model ||
          "openai"
      ),
      reasonerModel: String(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.model as string) ||
          audit_entry.extra?.model ||
          explanation?.llm_model ||
          "gpt-4o-mini"
      ),
      isFallback: Boolean(
        ((audit_entry.extra?.reasoner as Record<string, unknown>)?.is_fallback as boolean) ??
          audit_entry.extra?.is_fallback ??
          false
      ),
      fallbackReason:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.fallback_reason as string) ||
          (audit_entry.extra?.fallback_reason as string) ||
          null),
      recommendations:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.recommendations as string[]) ||
          (audit_entry.extra?.recommendations as string[]) ||
          []),
      supportingEvidence:
        (((audit_entry.extra?.reasoner as Record<string, unknown>)?.supporting_evidence as string[]) ||
          (audit_entry.extra?.supporting_evidence as string[]) ||
          []),
      reasonerLatencyMs:
        typeof (audit_entry.extra?.reasoner as Record<string, unknown>)?.latency_ms === "number"
          ? ((audit_entry.extra?.reasoner as Record<string, unknown>).latency_ms as number)
          : typeof audit_entry.extra?.latency_ms === "number"
          ? (audit_entry.extra.latency_ms as number)
          : 28,
    },
    subsystems: updatedSubsystems,
  };
}

export function TelemetryProvider({ children }: { children: ReactNode }) {
  const [windowIndex, setWindowIndex] = useState<number>(0);
  const [backendWindow, setBackendWindow] = useState<MissionTelemetryWindow | null>(null);

  // Backend connection state
  const [apiStatus, setApiStatus] = useState<ApiConnectionState>("connecting");
  const [apiHealth, setApiHealth] = useState<HealthResponse | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // Analysis state
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [latestBackendResponse, setLatestBackendResponse] = useState<AnalyzeResponse | null>(null);
  const [lastAnalysisError, setLastAnalysisError] = useState<string | null>(null);

  // Historical Replay state
  const [replayCatalog, setReplayCatalog] = useState<ReplayCatalogDto | null>(null);
  const [replayStatus, setReplayStatus] = useState<ReplayStatusDto | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<"SMAP" | "MSL">("SMAP");
  const [selectedSplit, setSelectedSplit] = useState<"train" | "test">("test");
  const [selectedChannel, setSelectedChannel] = useState<string>("P-1");
  const [replaySpeedMs, setReplaySpeedMs] = useState<number>(500);
  const [pauseOnAnomaly, setPauseOnAnomaly] = useState<boolean>(true);
  const [replayError, setReplayError] = useState<string | null>(null);

  const isReplaying = replayStatus?.status === "running" || replayStatus?.status === "paused";
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Runs state
  const [runs, setRuns] = useState<RunManifestDto[]>([]);
  const [activeRunDetails, setActiveRunDetails] = useState<RunDetailsDto | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState<boolean>(false);

  // Effective current window: uses active backend analysis if available, otherwise simulated replay window
  const simulatedWindow = MOCK_WINDOWS[windowIndex] || MOCK_WINDOWS[0];
  const currentWindow = backendWindow || {
    ...simulatedWindow,
    dataSource: "simulated" as const,
  };
  const totalWindows = replayStatus && replayStatus.total_windows > 0 ? replayStatus.total_windows : MOCK_WINDOWS.length;

  const nextWindow = () => {
    setBackendWindow(null);
    setWindowIndex((prev) => (prev < totalWindows - 1 ? prev + 1 : prev));
  };

  const prevWindow = () => {
    setBackendWindow(null);
    setWindowIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const resetToSimulated = () => {
    setBackendWindow(null);
    if (replayStatus?.status === "running" || replayStatus?.status === "paused") {
      stopHistoricalReplay().catch(() => {});
    }
  };

  // Check backend health
  const refreshHealth = useCallback(async () => {
    try {
      setApiStatus("connecting");
      const health = await getHealth();
      setApiHealth(health);
      setApiStatus("connected");
      setApiError(null);
    } catch (err: unknown) {
      setApiStatus("disconnected");
      setApiHealth(null);
      setApiError(err instanceof Error ? err.message : "Failed to connect to FastAPI backend");
    }
  }, []);

  // Fetch replay catalog
  const refreshReplayCatalog = useCallback(async () => {
    try {
      const catalog = await getReplayCatalog();
      setReplayCatalog(catalog);
      // If selected channel not in dataset, reset to first available
      const dsChannels = catalog.datasets[selectedDataset]?.channels || [];
      if (dsChannels.length > 0 && !dsChannels.some((c) => c.id === selectedChannel)) {
        setSelectedChannel(dsChannels[0].id);
      }
    } catch (err: unknown) {
      console.warn("Could not retrieve replay catalog:", err);
    }
  }, [selectedDataset, selectedChannel]);

  // List experimental runs
  const refreshRuns = useCallback(async () => {
    try {
      setIsLoadingRuns(true);
      const fetchedRuns = await listRuns();
      setRuns(fetchedRuns);
    } catch (err: unknown) {
      console.warn("Could not retrieve experiment runs:", err);
    } finally {
      setIsLoadingRuns(false);
    }
  }, []);

  const handleSelectChannel = useCallback((channel: string) => {
    setSelectedChannel(channel);
    setBackendWindow(null);
    setLatestBackendResponse(null);
    setReplayError(null);
    setReplayStatus(null);
  }, []);

  const handleSelectDataset = useCallback((dataset: "SMAP" | "MSL") => {
    setSelectedDataset(dataset);
    setBackendWindow(null);
    setLatestBackendResponse(null);
    setReplayError(null);
    setReplayStatus(null);
  }, []);

  const handleSelectSplit = useCallback((split: "train" | "test") => {
    setSelectedSplit(split);
    setBackendWindow(null);
    setLatestBackendResponse(null);
    setReplayError(null);
    setReplayStatus(null);
  }, []);

  const handleSetReplaySpeedMs = useCallback(
    async (ms: number) => {
      setReplaySpeedMs(ms);
      if (replayStatus?.status === "running" || replayStatus?.status === "paused") {
        try {
          const updated = await updateReplayConfig({ speed_delay_ms: ms });
          setReplayStatus(updated);
        } catch (err) {
          console.warn("Failed to update replay speed config:", err);
        }
      }
    },
    [replayStatus?.status]
  );

  const togglePauseOnAnomaly = useCallback(
    async (enabled: boolean) => {
      setPauseOnAnomaly(enabled);
      if (replayStatus?.status === "running" || replayStatus?.status === "paused") {
        try {
          const updated = await updateReplayConfig({ pause_on_anomaly: enabled });
          setReplayStatus(updated);
          if (updated.latest_analysis && updated.latest_window) {
            const mapped = mapReplayStatusToWindow(updated, simulatedWindow);
            if (mapped) {
              setBackendWindow(mapped);
              setWindowIndex(updated.current_window_index);
            }
          }
        } catch (err) {
          console.warn("Failed to sync pause_on_anomaly config:", err);
        }
      }
    },
    [replayStatus?.status, simulatedWindow]
  );

  // Start Historical Replay
  const startHistoricalReplay = useCallback(
    async (startWindow?: number, pauseOnAnom?: boolean) => {
      try {
        const effectivePauseOnAnom = pauseOnAnom !== undefined ? pauseOnAnom : pauseOnAnomaly;
        setReplayError(null);
        setBackendWindow(null);
        setLatestBackendResponse(null);
        const initialStatus = await startReplay({
          dataset: selectedDataset,
          split: selectedSplit,
          channel: selectedChannel,
          window_size: 100,
          stride: 10,
          speed_delay_ms: replaySpeedMs,
          start_window: startWindow,
          pause_on_anomaly: effectivePauseOnAnom,
        });
        setReplayStatus(initialStatus);
        setApiStatus("connected");

        if (initialStatus.latest_analysis && initialStatus.latest_window) {
          const mapped = mapReplayStatusToWindow(initialStatus, simulatedWindow);
          if (mapped) {
            setBackendWindow(mapped);
            setWindowIndex(initialStatus.current_window_index);
          }
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to start historical replay";
        setReplayError(msg);
        console.error(msg);
      }
    },
    [selectedDataset, selectedSplit, selectedChannel, replaySpeedMs, pauseOnAnomaly, simulatedWindow]
  );

  // Pause Historical Replay
  const pauseHistoricalReplay = useCallback(async () => {
    try {
      const updated = await pauseReplay();
      setReplayStatus(updated);
    } catch (err: unknown) {
      console.warn("Failed to pause replay:", err);
    }
  }, []);

  // Resume Historical Replay
  const resumeHistoricalReplay = useCallback(async () => {
    try {
      const updated = await resumeReplay();
      setReplayStatus(updated);
      if (updated.latest_analysis && updated.latest_window) {
        const mapped = mapReplayStatusToWindow(updated, simulatedWindow);
        if (mapped) {
          setBackendWindow(mapped);
          setWindowIndex(updated.current_window_index);
        }
      }
    } catch (err: unknown) {
      console.warn("Failed to resume replay:", err);
    }
  }, [simulatedWindow]);

  // Stop Historical Replay
  const stopHistoricalReplay = useCallback(async () => {
    try {
      const updated = await stopReplay();
      setReplayStatus(updated);
    } catch (err: unknown) {
      console.warn("Failed to stop replay:", err);
    }
  }, []);

  // Polling loop for active historical replay
  useEffect(() => {
    if (replayStatus?.status === "running") {
      pollingRef.current = setInterval(async () => {
        try {
          const status = await getReplayStatus();
          setReplayStatus(status);

          if (status.latest_analysis && status.latest_window) {
            const mapped = mapReplayStatusToWindow(status, simulatedWindow);
            if (mapped) {
              setBackendWindow(mapped);
              setWindowIndex(status.current_window_index);
            }
          }

          if (status.status === "completed" || status.status === "stopped" || status.status === "error") {
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
          }
        } catch (err) {
          console.warn("Replay status poll error:", err);
        }
      }, Math.max(250, replaySpeedMs > 0 ? replaySpeedMs / 2 : 300));
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [replayStatus?.status, replaySpeedMs, simulatedWindow]);

  // Retrieve details for a specific run
  const selectRun = useCallback(async (runId: string): Promise<RunDetailsDto | null> => {
    try {
      const details = await getRunDetails(runId);
      setActiveRunDetails(details);
      return details;
    } catch (err: unknown) {
      console.warn(`Could not retrieve run details for ${runId}:`, err);
      return null;
    }
  }, []);

  // Retrieve single audit entry by UUID
  const fetchAuditById = useCallback(async (entryId: string): Promise<AuditEntryDto | null> => {
    try {
      return await getAuditEntry(entryId);
    } catch (err: unknown) {
      console.warn(`Could not retrieve audit entry ${entryId}:`, err);
      return null;
    }
  }, []);

  // Submit single telemetry window to POST /analyze
  const runAnalysis = useCallback(
    async (
      payloadOrScenario: "nominal" | "powerAnomaly" | "thermalAnomaly" | TelemetryWindowRequest = "powerAnomaly"
    ): Promise<AnalyzeResponse | null> => {
      setIsAnalyzing(true);
      setLastAnalysisError(null);

      let payload: TelemetryWindowRequest;
      if (typeof payloadOrScenario === "string") {
        payload = DEMO_TELEMETRY_PAYLOADS[payloadOrScenario] || DEMO_TELEMETRY_PAYLOADS.powerAnomaly;
      } else {
        payload = payloadOrScenario;
      }

      try {
        const response = await analyzeTelemetry(payload);
        setLatestBackendResponse(response);
        setApiStatus("connected");

        // Map live response into the active window state
        const mappedWindow = mapBackendResponseToWindow(response, payload, simulatedWindow);
        setBackendWindow(mappedWindow);

        // Refresh runs list to include any new executions
        refreshRuns().catch(() => {});

        return response;
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : "Pipeline analysis request failed";
        setLastAnalysisError(errMsg);
        setApiError(errMsg);
        return null;
      } finally {
        setIsAnalyzing(false);
      }
    },
    [simulatedWindow, refreshRuns]
  );

  // Initial mount check
  useEffect(() => {
    refreshHealth();
    refreshReplayCatalog();
    refreshRuns();
  }, [refreshHealth, refreshReplayCatalog, refreshRuns]);

  const exportAuditReport = () => {
    const reportData = {
      source:
        currentWindow.dataSource === "backend"
          ? `FASTAPI_BACKEND_${replayStatus?.status === "running" ? "HISTORICAL_REPLAY" : "POST_ANALYZE"}`
          : "SIMULATED_REPLAY",
      windowId: currentWindow.windowId,
      windowIndex: currentWindow.windowIndex,
      timestamp: currentWindow.timestamp,
      met: currentWindow.met,
      status: currentWindow.status,
      groundTruth: currentWindow.groundTruth,
      fusionDecision: currentWindow.fusionDecision,
      auditLog: currentWindow.auditLog,
      groundingVerification: currentWindow.groundingVerification,
      subsystems: Object.fromEntries(
        Object.entries(currentWindow.subsystems).map(([k, v]) => [
          k,
          {
            score: v.anomalyScore,
            threshold: v.threshold,
            severity: v.severity,
            responsibleChannels: v.responsibleChannels,
            model: v.model,
          },
        ])
      ),
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sentinel_audit_win_${1000 + currentWindow.windowIndex}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <TelemetryContext.Provider
      value={{
        windowIndex,
        currentWindow,
        totalWindows,
        setWindowIndex: (idx) => {
          setBackendWindow(null);
          setWindowIndex(idx);
        },
        nextWindow,
        prevWindow,
        exportAuditReport,
        apiStatus,
        apiHealth,
        apiError,
        refreshHealth,
        isAnalyzing,
        latestBackendResponse,
        lastAnalysisError,
        runAnalysis,
        resetToSimulated,
        replayCatalog,
        replayStatus,
        selectedDataset,
        selectedSplit,
        selectedChannel,
        replaySpeedMs,
        pauseOnAnomaly,
        isReplaying,
        replayError,
        setSelectedDataset: handleSelectDataset,
        setSelectedSplit: handleSelectSplit,
        setSelectedChannel: handleSelectChannel,
        setReplaySpeedMs: handleSetReplaySpeedMs,
        togglePauseOnAnomaly,
        startHistoricalReplay,
        pauseHistoricalReplay,
        resumeHistoricalReplay,
        stopHistoricalReplay,
        refreshReplayCatalog,
        runs,
        activeRunDetails,
        isLoadingRuns,
        refreshRuns,
        selectRun,
        fetchAuditById,
      }}
    >
      {children}
    </TelemetryContext.Provider>
  );
}

export function useTelemetry(): TelemetryContextType {
  const context = useContext(TelemetryContext);
  if (!context) {
    throw new Error("useTelemetry must be used within a TelemetryProvider");
  }
  return context;
}
