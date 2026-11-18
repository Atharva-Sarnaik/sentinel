/**
 * lib/api/services.ts
 * ===================
 * Typed API service functions for Sentinel endpoints.
 */

import { apiClient } from "./client";
import {
  AnalyzeResponse,
  AuditEntryDto,
  HealthResponse,
  ReplayCatalogDto,
  ReplayStartPayload,
  ReplayStatusDto,
  RunDetailsDto,
  RunManifestDto,
  TelemetryWindowRequest,
} from "./types";

/**
 * Service health check endpoint (`GET /health`).
 */
export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/health");
}

/**
 * Submit a TelemetryWindow payload for multi-agent health analysis (`POST /analyze`).
 */
export async function analyzeTelemetry(
  payload: TelemetryWindowRequest
): Promise<AnalyzeResponse> {
  return apiClient<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * List all saved experimental run manifests (`GET /runs`).
 */
export async function listRuns(): Promise<RunManifestDto[]> {
  return apiClient<RunManifestDto[]>("/runs");
}

/**
 * Retrieve RunManifest and metrics.json for a specific experiment run ID (`GET /runs/{run_id}`).
 */
export async function getRunDetails(runId: string): Promise<RunDetailsDto> {
  return apiClient<RunDetailsDto>(`/runs/${encodeURIComponent(runId)}`);
}

/**
 * Retrieve an immutable AuditEntry by its unique entry ID (`GET /audit/{entry_id}`).
 */
export async function getAuditEntry(entryId: string): Promise<AuditEntryDto> {
  return apiClient<AuditEntryDto>(`/audit/${encodeURIComponent(entryId)}`);
}

/**
 * Retrieve full catalog of available NASA SMAP and MSL channels (`GET /replay/channels`).
 */
export async function getReplayCatalog(): Promise<ReplayCatalogDto> {
  return apiClient<ReplayCatalogDto>("/replay/channels");
}

/**
 * Query active historical replay status, progress, and latest analysis (`GET /replay/status`).
 */
export async function getReplayStatus(): Promise<ReplayStatusDto> {
  return apiClient<ReplayStatusDto>("/replay/status");
}

/**
 * Start a historical telemetry replay session (`POST /replay/start`).
 */
export async function startReplay(payload: ReplayStartPayload): Promise<ReplayStatusDto> {
  return apiClient<ReplayStatusDto>("/replay/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Pause active historical telemetry replay (`POST /replay/pause`).
 */
export async function pauseReplay(): Promise<ReplayStatusDto> {
  return apiClient<ReplayStatusDto>("/replay/pause", {
    method: "POST",
  });
}

/**
 * Resume active historical telemetry replay (`POST /replay/resume`).
 */
export async function resumeReplay(): Promise<ReplayStatusDto> {
  return apiClient<ReplayStatusDto>("/replay/resume", {
    method: "POST",
  });
}

/**
 * Stop and terminate active historical telemetry replay (`POST /replay/stop`).
 */
export async function stopReplay(): Promise<ReplayStatusDto> {
  return apiClient<ReplayStatusDto>("/replay/stop", {
    method: "POST",
  });
}

/**
 * Standard synthetic demonstration windows conforming to the TelemetryWindow contract.
 * Note: These are explicitly labeled as synthetic demo payloads for testing and demonstration.
 */
export const DEMO_TELEMETRY_PAYLOADS: Record<string, TelemetryWindowRequest> = {
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
    metadata: {
      scenario: "Nominal Orbit Steady State",
      description: "All channels within normal baseline corridors",
    },
  },
  powerAnomaly: {
    subsystem: "power",
    start_time: "2025-05-18T14:22:00Z",
    end_time: "2025-05-18T14:26:00Z",
    channels: {
      "P-1": [28.40, 48.72, 49.50, 52.10], // Exceeds safety threshold (>40.0)
      "P-2": [14.12, 14.15, 14.18, 14.14],
      "T-1": [21.10, 21.20, 21.15, 21.25],
      "A-1": [0.018, 0.020, 0.019, 0.021],
      "C-1": [-82.4, -82.1, -82.3, -82.0],
    },
    source_dataset: "Synthetic-Demonstration-LEO",
    metadata: {
      scenario: "EPS Main Bus Overvoltage Excursion",
      description: "Severe P-1 bus spike triggering critical alert and cross-agent corroboration",
    },
  },
  thermalAnomaly: {
    subsystem: "thermal",
    start_time: "2025-05-18T14:22:00Z",
    end_time: "2025-05-18T14:26:00Z",
    channels: {
      "P-1": [28.40, 28.42, 28.39, 28.41],
      "P-2": [14.12, 14.15, 14.18, 14.14],
      "T-1": [21.10, 45.30, 58.70, 74.20], // Exceeds safety threshold (>40.0)
      "A-1": [0.018, 0.020, 0.019, 0.021],
      "C-1": [-82.4, -82.1, -82.3, -82.0],
    },
    source_dataset: "Synthetic-Demonstration-LEO",
    metadata: {
      scenario: "Radiator Thermal Runaway",
      description: "T-1 payload bay temperature excursion",
    },
  },
};
