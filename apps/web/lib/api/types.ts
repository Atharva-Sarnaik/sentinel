/**
 * lib/api/types.ts
 * =================
 * Strict TypeScript models matching Sentinel FastAPI schemas and frozen Pydantic contracts.
 */

export type Subsystem = "power" | "thermal" | "attitude" | "communications";
export type Severity = "nominal" | "advisory" | "warning" | "critical";
export type VerifierStatus = "grounded" | "ungrounded" | "abstained";

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  tier: string;
}

export interface TelemetryWindowRequest {
  window_id?: string;
  subsystem: Subsystem;
  start_time: string;
  end_time: string;
  channels: Record<string, number[]>;
  source_dataset: string;
  metadata?: Record<string, unknown>;
}

export interface SpecialistOpinionDto {
  opinion_id: string;
  window_id: string;
  subsystem: Subsystem;
  anomaly_score: number;
  severity: Severity;
  responsible_channels: string[];
  threshold_used: number;
  model_run_id: string;
  created_at: string;
}

export interface FusionDecisionDto {
  decision_id: string;
  window_id: string;
  opinions: SpecialistOpinionDto[];
  severity: Severity;
  corroborating_subsystems: Subsystem[];
  attributed_subsystem: Subsystem | null;
  fusion_rule_applied: string;
  created_at: string;
}

export interface ExplanationDto {
  explanation_id: string;
  decision_id: string;
  text: string;
  cited_channels: string[];
  cited_severity: Severity;
  prompt_version: string;
  llm_model: string;
  created_at: string;
}

export interface VerifierResultDto {
  verifier_id: string;
  explanation_id: string;
  status: VerifierStatus;
  ungrounded_claims: string[];
  retry_count: number;
  created_at: string;
}

export interface AuditEntryDto {
  entry_id: string;
  run_id: string;
  window_id: string;
  decision_id: string;
  verifier_id: string;
  final_severity: Severity;
  abstained: boolean;
  created_at: string;
  extra: Record<string, unknown>;
}

export interface AnalyzeResponse {
  decision: FusionDecisionDto;
  explanation: ExplanationDto | null;
  verifier_result: VerifierResultDto;
  audit_entry: AuditEntryDto;
  abstained: boolean;
}

export interface RunManifestDto {
  run_id: string;
  description: string;
  dataset_dvc_hash: string;
  config_hash: string;
  mlflow_experiment_id: string;
  mlflow_run_ids: Record<string, string>;
  created_at: string;
  git_commit?: string | null;
  artifact_dir?: string | null;
}

export interface RunDetailsDto {
  manifest: RunManifestDto;
  metrics: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Historical Replay Types (Phase 3)
// ---------------------------------------------------------------------------

export type ReplayState = "idle" | "running" | "paused" | "stopped" | "completed" | "error";

export interface ReplayChannelDto {
  id: string;
  subsystem: Subsystem;
  has_train: boolean;
  has_test: boolean;
  anomaly_count: number;
  anomaly_intervals: [number, number][];
}

export interface ReplayDatasetDto {
  splits: ("train" | "test")[];
  channels: ReplayChannelDto[];
  total_channels: number;
}

export interface ReplayCatalogDto {
  datasets: {
    SMAP?: ReplayDatasetDto;
    MSL?: ReplayDatasetDto;
    [key: string]: ReplayDatasetDto | undefined;
  };
}

export interface ReplayWindowSummary {
  window_id: string;
  start_time: string;
  end_time: string;
  subsystem: Subsystem;
  channel: string;
  primary_series: number[];
  is_anomalous: boolean;
  metadata: Record<string, unknown>;
}

export interface ReplayHistoryItem {
  window_index: number;
  window_id: string;
  timestamp: string;
  severity: Severity;
  attributed_subsystem: Subsystem | null;
  fusion_rule: string;
  audit_entry_id: string;
  is_ground_truth_anomalous: boolean;
  explanation_snippet: string;
}

export interface ReplayStatusDto {
  session_id: string | null;
  status: ReplayState;
  dataset: "SMAP" | "MSL";
  split: "train" | "test";
  channel: string;
  subsystem: Subsystem;
  window_size: number;
  stride: number;
  speed_delay_ms: number;
  current_window_index: number;
  total_windows: number;
  processed_windows: number;
  failed_windows: number;
  progress_percent: number;
  is_anomalous: boolean | null;
  latest_window: ReplayWindowSummary | null;
  latest_analysis: AnalyzeResponse | null;
  recent_history: ReplayHistoryItem[];
  error: string | null;
}

export interface ReplayStartPayload {
  dataset: string;
  split: string;
  channel: string;
  window_size?: number;
  stride?: number;
  speed_delay_ms?: number;
  max_windows?: number | null;
  start_window?: number;
  pause_on_anomaly?: boolean;
}

export class ApiClientError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number = 500, details?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.details = details;
  }
}
