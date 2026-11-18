export type SubsystemType = "power" | "thermal" | "attitude" | "communications";
export type SeverityType = "nominal" | "advisory" | "warning" | "critical";

export interface ChannelData {
  id: string;
  name: string;
  unit: string;
  baseline: string;
  limit: string;
  currentValue: number;
  mean: number;
  stdDev: number;
  isAnomalous: boolean;
  history: number[];
}

export interface SubsystemTelemetry {
  id: SubsystemType;
  name: string;
  code: string;
  icon: string;
  model: string;
  anomalyScore: number;
  threshold: number;
  severity: SeverityType;
  responsibleChannels: string[];
  channels: Record<string, ChannelData>;
  sparkline: number[];
}

export interface MissionTelemetryWindow {
  windowIndex: number;
  windowId: string;
  timestamp: string;
  met: string;
  status: "NORMAL" | "ANOMALOUS";
  groundTruth: boolean;
  cohesionIndex: number;
  bayesianAnomalyProb: number;
  activeAnomaliesCount: number;
  dataSource?: "backend" | "simulated";
  backendRunId?: string;
  groundingVerification: {
    status: "GROUNDED" | "ABSTAINED";
    retries: number;
    latencyMs: number;
  };
  auditLog: {
    entryId: string;
    decisionId: string;
    hash: string;
    status: "COMMITTED" | "PENDING";
    timestamp: string;
  };
  fusionDecision: {
    severity: SeverityType;
    corroborationRule: string;
    concurrenceRatio: string;
    attributedSubsystem: string;
    explanationText: string;
    citedChannels: string[];
    citedSeverity: SeverityType;
    consensusEntropy: number;
    reasonerProvider?: string;
    reasonerModel?: string;
    isFallback?: boolean;
    fallbackReason?: string | null;
    recommendations?: string[];
    supportingEvidence?: string[];
    reasonerLatencyMs?: number;
  };
  subsystems: {
    power: SubsystemTelemetry;
    thermal: SubsystemTelemetry;
    attitude: SubsystemTelemetry;
    communications: SubsystemTelemetry;
  };
}
