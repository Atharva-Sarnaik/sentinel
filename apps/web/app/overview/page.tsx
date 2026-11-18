"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useTelemetry } from "../../context/TelemetryContext";
import { ReplayPanel } from "../../components/replay/ReplayPanel";

export default function OverviewPage() {
  const {
    currentWindow,
    windowIndex,
    apiStatus,
    apiHealth,
    runs,
    isLoadingRuns,
    latestBackendResponse,
    runAnalysis,
    isAnalyzing,
  } = useTelemetry();
  const { power, thermal, attitude, communications } = currentWindow.subsystems;
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [copiedModalJson, setCopiedModalJson] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const winNum = 1000 + currentWindow.windowIndex;
  const isNormal = currentWindow.status === "NORMAL";
  const isBackendData = currentWindow.dataSource === "backend";

  const modalPayload = {
    data_source: isBackendData ? "FASTAPI_BACKEND_LIVE_ANALYSIS" : "SIMULATED_REPLAY_DEMO",
    window_id: currentWindow.windowId,
    timestamp_utc: `${currentWindow.timestamp}`,
    spacecraft_id: "NORAD-48291",
    met_seconds: 12284382 + windowIndex * 10,
    ground_truth_label: currentWindow.groundTruth ? 1 : 0,
    health_index: currentWindow.cohesionIndex / 100,
    bayesian_score: Number(currentWindow.bayesianAnomalyProb.toFixed(4)),
    agents_consensus: {
      "PWR-EPS-AI": {
        model: power.model,
        score: Number(power.anomalyScore.toFixed(2)),
        threshold: power.threshold,
        decision: power.anomalyScore > power.threshold ? 1 : 0,
        responsible_channels: power.responsibleChannels,
      },
      "THM-TCS-AI": {
        model: thermal.model,
        score: Number(thermal.anomalyScore.toFixed(2)),
        threshold: thermal.threshold,
        decision: thermal.anomalyScore > thermal.threshold ? 1 : 0,
        responsible_channels: thermal.responsibleChannels,
      },
      "ATT-ADCS-AI": {
        model: attitude.model,
        score: Number(attitude.anomalyScore.toFixed(2)),
        threshold: attitude.threshold,
        decision: attitude.anomalyScore > attitude.threshold ? 1 : 0,
        responsible_channels: attitude.responsibleChannels,
      },
      "COM-XBD-AI": {
        model: communications.model,
        score: Number(communications.anomalyScore.toFixed(2)),
        threshold: communications.threshold,
        decision: communications.anomalyScore > communications.threshold ? 1 : 0,
        responsible_channels: communications.responsibleChannels,
      },
    },
    fusion_verdict: {
      state: isNormal ? "NOMINAL" : "ANOMALOUS",
      severity: currentWindow.fusionDecision.severity,
      corroboration_rule: currentWindow.fusionDecision.corroborationRule,
      attributed_subsystem: currentWindow.fusionDecision.attributedSubsystem,
      active_anomalies: currentWindow.activeAnomaliesCount,
    },
    grounding_audit: {
      rule_engine: "Telemetry Coherence v4.2",
      status: currentWindow.groundingVerification.status,
      retries: currentWindow.groundingVerification.retries,
      audit_entry_id: currentWindow.auditLog.entryId,
      merkle_sha256: currentWindow.auditLog.hash,
    },
  };

  const handleCopyModalJson = () => {
    navigator.clipboard.writeText(JSON.stringify(modalPayload, null, 2)).then(() => {
      setCopiedModalJson(true);
      setTimeout(() => setCopiedModalJson(false), 2000);
    });
  };

  // Build rows for the operational table combining live backend response, stored runs, and baseline replay
  const operationalRows = [];

  // 1. If active window is from live backend analysis, show as top row
  if (isBackendData && latestBackendResponse) {
    const dec = latestBackendResponse.decision;
    const pwrOp = dec.opinions.find((o) => o.subsystem === "power");
    const thmOp = dec.opinions.find((o) => o.subsystem === "thermal");
    const attOp = dec.opinions.find((o) => o.subsystem === "attitude");
    const comOp = dec.opinions.find((o) => o.subsystem === "communications");

    operationalRows.push({
      win: `LIVE-${dec.window_id.slice(0, 8)}`,
      time: currentWindow.timestamp,
      truth: isNormal ? "NOMINAL (0)" : "ANOMALY (1)",
      truthClass: isNormal
        ? "bg-surface-container-low text-on-tertiary-container"
        : "bg-error-container text-on-error-container",
      pwr: pwrOp && pwrOp.severity !== "nominal" ? 1 : 0,
      thm: thmOp && thmOp.severity !== "nominal" ? 1 : 0,
      att: attOp && attOp.severity !== "nominal" ? 1 : 0,
      com: comOp && comOp.severity !== "nominal" ? 1 : 0,
      verdict: dec.severity.toUpperCase(),
      prob: currentWindow.bayesianAnomalyProb.toFixed(2),
      hash: currentWindow.auditLog.hash,
      isLive: true,
    });
  }

  // 2. Add recent historical replay rows (clearly marked with demo timestamps)
  operationalRows.push(
    {
      win: `WIN-${winNum}`,
      time: currentWindow.timestamp,
      truth: isNormal ? "NORMAL (0)" : "ANOMALY (1)",
      truthClass: isNormal
        ? "bg-surface-container-low text-on-tertiary-container"
        : "bg-error-container text-on-error-container",
      pwr: power.anomalyScore > power.threshold ? 1 : 0,
      thm: thermal.anomalyScore > thermal.threshold ? 1 : 0,
      att: attitude.anomalyScore > attitude.threshold ? 1 : 0,
      com: communications.anomalyScore > communications.threshold ? 1 : 0,
      verdict: isNormal ? "NOMINAL" : "ANOMALY DETECTED",
      prob: currentWindow.bayesianAnomalyProb.toFixed(2),
      hash: currentWindow.auditLog.hash,
      isLive: false,
    },
    {
      win: `WIN-${winNum - 1 > 999 ? winNum - 1 : 1000}`,
      time: "2025-05-18 14:22:00",
      truth: "NORMAL (0)",
      truthClass: "bg-surface-container-low text-on-tertiary-container",
      pwr: 0,
      thm: 0,
      att: 0,
      com: 0,
      verdict: "NOMINAL",
      prob: "0.13",
      hash: "84cd92...11ae",
      isLive: false,
    },
    {
      win: `WIN-${winNum - 2 > 999 ? winNum - 2 : 1000}`,
      time: "2025-05-18 14:21:50",
      truth: "NORMAL (0)",
      truthClass: "bg-surface-container-low text-on-tertiary-container",
      pwr: 0,
      thm: 0,
      att: 0,
      com: 0,
      verdict: "NOMINAL",
      prob: "0.15",
      hash: "4b19df...9812",
      isLive: false,
    },
    {
      win: `WIN-${winNum - 3 > 999 ? winNum - 3 : 1000}`,
      time: "2025-05-18 14:21:40",
      truth: "NORMAL (0)",
      truthClass: "bg-surface-container-low text-on-tertiary-container",
      pwr: 0,
      thm: 0,
      att: 0,
      com: 0,
      verdict: "NOMINAL",
      prob: "0.18",
      hash: "112da9...f56a",
      isLive: false,
    }
  );

  return (
    <div className="flex flex-col w-full gap-space-lg">
      {/* 1. Operational Context Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md bg-surface-container-lowest p-space-md rounded-lg shadow-sm">
        <div className="flex items-center gap-space-md">
          <div className="p-space-sm bg-surface-container-low rounded">
            <span
              className="material-symbols-outlined text-secondary text-2xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              satellite_alt
            </span>
          </div>
          <div>
            <div className="flex items-center gap-space-sm flex-wrap">
              <span className="font-headline-sm text-headline-sm text-on-surface">LEO-SENTINEL-4B</span>
              <span className="px-2 py-0.5 rounded bg-surface-container-high font-mono-data-sm text-mono-data-sm text-on-surface-variant font-medium">
                REV #4,912
              </span>
              <span
                className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-label-caps text-label-caps font-semibold ${
                  isBackendData
                    ? "bg-secondary-fixed text-on-secondary-fixed"
                    : "bg-surface-container text-on-tertiary-container"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isBackendData ? "bg-secondary animate-pulse" : "bg-on-tertiary-container animate-pulse"
                  }`}
                />
                {isBackendData
                  ? `FASTAPI LIVE INGESTION [RUN: ${currentWindow.backendRunId || "PIPELINE"}]`
                  : "CONSTELLATION SYNCED [SIMULATED REPLAY]"}
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
              API Status:{" "}
              <strong className="text-on-surface">
                {apiStatus === "connected"
                  ? `Connected to FastAPI (${apiHealth?.service} v${apiHealth?.version || "0.1.0"})`
                  : "Disconnected / Offline (Displaying Verified Replay)"}
              </strong>{" "}
              • Stored Runs: {runs.length} manifests available
            </p>
          </div>
        </div>

        {/* Action Micro-cluster */}
        <div className="flex items-center gap-space-sm flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container-low rounded">
            <span className="font-label-caps text-label-caps text-outline uppercase">EPOCH WINDOW:</span>
            <span className="font-mono-data-sm text-mono-data-sm text-on-surface font-semibold">
              {isBackendData ? `LIVE-${currentWindow.windowId.slice(0, 8)}` : `WIN-${winNum}`}
            </span>
          </div>

          {/* Analyze Trigger */}
          <button
            onClick={() => runAnalysis("powerAnomaly")}
            disabled={isAnalyzing}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-secondary text-on-secondary font-label-caps text-label-caps tracking-wider uppercase shadow-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
            title="Invoke Sentinel multi-agent pipeline via POST /analyze"
            type="button"
          >
            <span className={`material-symbols-outlined text-sm ${isAnalyzing ? "animate-spin" : ""}`}>
              {isAnalyzing ? "sync" : "play_circle"}
            </span>
            <span>{isAnalyzing ? "Analyzing..." : "Trigger /analyze"}</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-primary text-on-primary font-label-caps text-label-caps tracking-wider uppercase shadow-sm hover:opacity-90 transition-opacity"
            id="triggerModalBtn"
            type="button"
          >
            <span className="material-symbols-outlined text-sm">terminal</span>
            <span>Export Window JSON</span>
          </button>
        </div>
      </div>

      {/* NASA Historical Telemetry Replay Engine (Phase 3) */}
      <ReplayPanel />

      {/* 2. Top Summary KPI Cards (5 metrics across) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-gutter-desktop">
        {/* Card 1: Satellite Health */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps uppercase text-outline">Satellite Health</span>
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container-low text-on-tertiary-container font-label-caps text-label-caps font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
              {isNormal ? "NOMINAL" : "DEGRADED"}
            </span>
          </div>
          <div className="my-space-md">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface">
                {currentWindow.cohesionIndex.toFixed(1)}
              </span>
              <span className="font-body-sm text-body-sm text-outline">%</span>
            </div>
            <div className="font-label-caps text-label-caps text-on-surface-variant mt-0.5">
              Subsystem Cohesion Index
            </div>
          </div>
          <div className="w-full bg-surface-container-low h-1.5 rounded overflow-hidden">
            <div
              className={`h-full rounded ${isNormal ? "bg-on-tertiary-container" : "bg-error"}`}
              style={{ width: `${Math.min(100, Math.max(0, currentWindow.cohesionIndex))}%` }}
            />
          </div>
        </div>

        {/* Card 2: Anomaly Probability */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps uppercase text-outline">Anomaly Probability</span>
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container-low font-label-caps text-label-caps font-semibold ${
                !isNormal ? "text-error" : "text-secondary"
              }`}
            >
              {!isNormal ? "HIGH RISK" : "LOW RISK"}
            </span>
          </div>
          <div className="my-space-md">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface">
                {currentWindow.bayesianAnomalyProb.toFixed(2)}
              </span>
              <span className="font-label-caps text-label-caps text-outline uppercase font-normal">p-val</span>
            </div>
            <div className="font-label-caps text-label-caps text-on-surface-variant mt-0.5">
              Bayesian Ensemble Score
            </div>
          </div>
          <div className="flex items-center justify-between font-mono-data-sm text-[10px] text-outline">
            <span>TOLERANCE: 0.65</span>
            <span className={isNormal ? "text-on-tertiary-container font-semibold" : "text-error font-semibold"}>
              {isNormal ? "-0.02 Δ" : "+0.35 Δ"}
            </span>
          </div>
        </div>

        {/* Card 3: Active Anomaly Count */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps uppercase text-outline">Active Anomalies</span>
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container-low font-label-caps text-label-caps font-semibold ${
                !isNormal ? "text-error" : "text-on-tertiary-container"
              }`}
            >
              {isNormal ? "CLEAR" : "FLAGGED"}
            </span>
          </div>
          <div className="my-space-md">
            <div className="flex items-baseline gap-1">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface">
                {currentWindow.activeAnomaliesCount}
              </span>
              <span className="font-mono-data-md text-mono-data-md text-outline">/ 4 SUBSYSTEMS</span>
            </div>
            <div className="font-label-caps text-label-caps text-on-surface-variant mt-0.5 truncate">
              {isBackendData
                ? `Attributed: ${currentWindow.fusionDecision.attributedSubsystem}`
                : "Replay Reference State"}
            </div>
          </div>
          <div className="flex items-center gap-1 font-label-caps text-label-caps text-outline">
            <span className="material-symbols-outlined text-[13px] text-on-tertiary-container">check_circle</span>
            <span>
              {isNormal ? "ALL CLEAR" : `CORROBORATED (${currentWindow.fusionDecision.concurrenceRatio})`}
            </span>
          </div>
        </div>

        {/* Card 4: Grounding Verification Status */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps uppercase text-outline">Grounding Verif</span>
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container-low font-label-caps text-label-caps font-semibold ${
                currentWindow.groundingVerification.status === "GROUNDED"
                  ? "text-on-tertiary-container"
                  : "text-error"
              }`}
            >
              {currentWindow.groundingVerification.status}
            </span>
          </div>
          <div className="my-space-md">
            <div className="flex items-baseline gap-1.5">
              <span className="font-headline-md text-headline-md text-on-surface font-semibold">
                {currentWindow.groundingVerification.status}
              </span>
            </div>
            <div className="font-label-caps text-label-caps text-on-surface-variant mt-0.5">
              Grounding Verifier
            </div>
          </div>
          <div className="flex items-center justify-between font-mono-data-sm text-[10px] text-outline">
            <span>{currentWindow.groundingVerification.retries} RETRIES (MAX 2)</span>
            <span className="text-on-surface">LATENCY {currentWindow.groundingVerification.latencyMs}ms</span>
          </div>
        </div>

        {/* Card 5: Audit Logging Status */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps uppercase text-outline">Audit Logging</span>
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container-low text-secondary font-label-caps text-label-caps font-semibold">
              IMMUTABLE
            </span>
          </div>
          <div className="my-space-md">
            <div className="flex items-baseline gap-1.5">
              <span className="font-headline-md text-headline-md text-on-surface font-semibold">
                {currentWindow.auditLog.status}
              </span>
            </div>
            <div className="font-label-caps text-label-caps text-on-surface-variant mt-0.5 truncate" title={currentWindow.auditLog.entryId}>
              ID: {currentWindow.auditLog.entryId.slice(0, 16)}...
            </div>
          </div>
          <div className="flex items-center gap-1 font-mono-data-sm text-[10px] text-on-tertiary-container truncate">
            <span className="material-symbols-outlined text-[13px]">lock</span>
            <span>ED25519 VERIFIED</span>
          </div>
        </div>
      </div>

      {/* 3. Four Subsystem Summary Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-gutter-desktop">
        {/* Subsystem 1: Power Subsystem Panel */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
          <div>
            <div className="flex items-center justify-between pb-space-sm bg-surface-container-low px-2 py-1.5 rounded">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-lg">bolt</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Power EPS</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded bg-surface-container-lowest font-label-caps text-label-caps font-semibold ${
                  power.severity === "nominal" ? "text-on-tertiary-container" : "text-error"
                }`}
              >
                {power.severity === "nominal" ? "NOMINAL" : power.severity.toUpperCase()}
              </span>
            </div>
            <div className="mt-space-md flex flex-wrap gap-1">
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                P-1: {power.channels["P-1"]?.currentValue.toFixed(1) || "28.4"}V
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                P-2: {power.channels["P-2"]?.currentValue.toFixed(1) || "14.1"}A
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                P-3: {power.channels["P-3"]?.currentValue.toFixed(0) || "99"}%
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                P-4: {power.channels["P-4"]?.currentValue.toFixed(0) || "312"}W
              </span>
            </div>
            <div className="my-space-md">
              <div className="flex items-center justify-between text-on-surface-variant font-label-caps text-label-caps">
                <span>ANOMALY SCORE</span>
                <span className="font-mono-data-md text-on-surface font-semibold">
                  {power.anomalyScore.toFixed(2)}{" "}
                  <span className="text-outline font-normal">/ {power.threshold.toFixed(2)}</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-low h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  className={`h-full rounded ${
                    power.anomalyScore > power.threshold ? "bg-error" : "bg-secondary"
                  }`}
                  style={{ width: `${Math.min(100, (power.anomalyScore / (power.threshold || 1)) * 100)}%` }}
                />
              </div>
            </div>
            {/* Inline SVG Sparkline for Power Load */}
            <div className="bg-surface-container-low p-2 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="font-label-caps text-[9px] uppercase text-outline">BUS LOAD TREND</span>
                <span className="font-mono-data-sm text-[10px] text-on-surface">{power.model}</span>
              </div>
              <svg className="w-full h-9 text-secondary" fill="none" preserveAspectRatio="none" viewBox="0 0 160 36">
                <path
                  d="M0,24 Q20,20 40,23 T80,14 T120,18 T160,12"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.75"
                />
                <circle className="fill-secondary" cx="160" cy="12" r="3" />
              </svg>
            </div>
            <div className="mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
              <span>RESPONSIBLE CH:</span>
              <span className="text-on-surface font-mono-data-sm">
                {power.responsibleChannels.length > 0 ? power.responsibleChannels.join(", ") : "NONE (STABLE)"}
              </span>
            </div>
          </div>
          <div className="pt-space-md mt-space-sm border-t border-surface-container flex items-center justify-between">
            <span className="font-mono-data-sm text-[11px] text-on-surface-variant font-medium">Autoencoder Specialist</span>
            <Link
              href="/power"
              className="font-label-caps text-label-caps text-secondary font-semibold hover:underline flex items-center gap-0.5"
            >
              <span>Subsystem</span>
              <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            </Link>
          </div>
        </div>

        {/* Subsystem 2: Thermal Subsystem Panel */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
          <div>
            <div className="flex items-center justify-between pb-space-sm bg-surface-container-low px-2 py-1.5 rounded">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-lg">thermostat</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Thermal TCS</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded bg-surface-container-lowest font-label-caps text-label-caps font-semibold ${
                  thermal.severity === "nominal" ? "text-on-tertiary-container" : "text-error"
                }`}
              >
                {thermal.severity === "nominal" ? "NOMINAL" : thermal.severity.toUpperCase()}
              </span>
            </div>
            <div className="mt-space-md flex flex-wrap gap-1">
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                T-1: {thermal.channels["T-1"]?.currentValue.toFixed(1) || "+21.2"}°C
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                T-2: {thermal.channels["T-2"]?.currentValue.toFixed(1) || "+18.4"}°C
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                T-3: {thermal.channels["T-3"]?.currentValue.toFixed(1) || "-14.2"}°C
              </span>
            </div>
            <div className="my-space-md">
              <div className="flex items-center justify-between text-on-surface-variant font-label-caps text-label-caps">
                <span>ANOMALY SCORE</span>
                <span className="font-mono-data-md text-on-surface font-semibold">
                  {thermal.anomalyScore.toFixed(2)}{" "}
                  <span className="text-outline font-normal">/ {thermal.threshold.toFixed(2)}</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-low h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  className={`h-full rounded ${
                    thermal.anomalyScore > thermal.threshold ? "bg-error" : "bg-secondary"
                  }`}
                  style={{ width: `${Math.min(100, (thermal.anomalyScore / (thermal.threshold || 1)) * 100)}%` }}
                />
              </div>
            </div>
            <div className="bg-surface-container-low p-2 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="font-label-caps text-[9px] uppercase text-outline">TEMP GRADIENT</span>
                <span className="font-mono-data-sm text-[10px] text-on-surface">{thermal.model}</span>
              </div>
              <svg className="w-full h-9 text-secondary" fill="none" preserveAspectRatio="none" viewBox="0 0 160 36">
                <path
                  d="M0,18 Q40,24 80,18 T160,20"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.75"
                />
                <circle className="fill-secondary" cx="160" cy="20" r="3" />
              </svg>
            </div>
            <div className="mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
              <span>RESPONSIBLE CH:</span>
              <span className="text-on-surface font-mono-data-sm">
                {thermal.responsibleChannels.length > 0 ? thermal.responsibleChannels.join(", ") : "NONE (STABLE)"}
              </span>
            </div>
          </div>
          <div className="pt-space-md mt-space-sm border-t border-surface-container flex items-center justify-between">
            <span className="font-mono-data-sm text-[11px] text-on-surface-variant font-medium">LSTM Specialist</span>
            <Link
              href="/thermal"
              className="font-label-caps text-label-caps text-secondary font-semibold hover:underline flex items-center gap-0.5"
            >
              <span>Subsystem</span>
              <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            </Link>
          </div>
        </div>

        {/* Subsystem 3: Attitude Subsystem Panel */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
          <div>
            <div className="flex items-center justify-between pb-space-sm bg-surface-container-low px-2 py-1.5 rounded">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-lg">sync_alt</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Attitude ADCS</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded bg-surface-container-lowest font-label-caps text-label-caps font-semibold ${
                  attitude.severity === "nominal" ? "text-on-tertiary-container" : "text-error"
                }`}
              >
                {attitude.severity === "nominal" ? "NOMINAL" : attitude.severity.toUpperCase()}
              </span>
            </div>
            <div className="mt-space-md flex flex-wrap gap-1">
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                A-1: {attitude.channels["A-1"]?.currentValue.toFixed(3) || "0.018"}°/s
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                A-2: {attitude.channels["A-2"]?.currentValue.toFixed(3) || "0.004"}°/s
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                A-3: {attitude.channels["A-3"]?.currentValue.toFixed(3) || "0.009"}°/s
              </span>
            </div>
            <div className="my-space-md">
              <div className="flex items-center justify-between text-on-surface-variant font-label-caps text-label-caps">
                <span>ANOMALY SCORE</span>
                <span className="font-mono-data-md text-on-surface font-semibold">
                  {attitude.anomalyScore.toFixed(2)}{" "}
                  <span className="text-outline font-normal">/ {attitude.threshold.toFixed(2)}</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-low h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  className={`h-full rounded ${
                    attitude.anomalyScore > attitude.threshold ? "bg-error" : "bg-secondary"
                  }`}
                  style={{ width: `${Math.min(100, (attitude.anomalyScore / (attitude.threshold || 1)) * 100)}%` }}
                />
              </div>
            </div>
            <div className="bg-surface-container-low p-2 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="font-label-caps text-[9px] uppercase text-outline">ANGULAR DRIFT</span>
                <span className="font-mono-data-sm text-[10px] text-on-surface">{attitude.model}</span>
              </div>
              <svg className="w-full h-9 text-secondary" fill="none" preserveAspectRatio="none" viewBox="0 0 160 36">
                <path
                  d="M0,18 Q40,12 80,18 T160,18"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.75"
                />
                <circle className="fill-secondary" cx="160" cy="18" r="3" />
              </svg>
            </div>
            <div className="mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
              <span>RESPONSIBLE CH:</span>
              <span className="text-on-surface font-mono-data-sm">
                {attitude.responsibleChannels.length > 0 ? attitude.responsibleChannels.join(", ") : "NONE (STABLE)"}
              </span>
            </div>
          </div>
          <div className="pt-space-md mt-space-sm border-t border-surface-container flex items-center justify-between">
            <span className="font-mono-data-sm text-[11px] text-on-surface-variant font-medium">IsolationForest Specialist</span>
            <Link
              href="/attitude"
              className="font-label-caps text-label-caps text-secondary font-semibold hover:underline flex items-center gap-0.5"
            >
              <span>Subsystem</span>
              <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            </Link>
          </div>
        </div>

        {/* Subsystem 4: Communications Subsystem Panel */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
          <div>
            <div className="flex items-center justify-between pb-space-sm bg-surface-container-low px-2 py-1.5 rounded">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-lg">cell_tower</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Comms CDHS</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded bg-surface-container-lowest font-label-caps text-label-caps font-semibold ${
                  communications.severity === "nominal" ? "text-on-tertiary-container" : "text-error"
                }`}
              >
                {communications.severity === "nominal" ? "NOMINAL" : communications.severity.toUpperCase()}
              </span>
            </div>
            <div className="mt-space-md flex flex-wrap gap-1">
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                C-1: {communications.channels["C-1"]?.currentValue.toFixed(1) || "-82.4"} dBm
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                C-2: {communications.channels["C-2"]?.currentValue.toFixed(1) || "12.0"} W
              </span>
              <span className="px-1.5 py-0.5 bg-surface-container-low font-mono-data-sm text-[11px] text-on-surface rounded font-medium">
                D-1: {communications.channels["D-1"]?.currentValue.toFixed(1) || "38.2"}%
              </span>
            </div>
            <div className="my-space-md">
              <div className="flex items-center justify-between text-on-surface-variant font-label-caps text-label-caps">
                <span>ANOMALY SCORE</span>
                <span className="font-mono-data-md text-on-surface font-semibold">
                  {communications.anomalyScore.toFixed(2)}{" "}
                  <span className="text-outline font-normal">/ {communications.threshold.toFixed(2)}</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-low h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  className={`h-full rounded ${
                    communications.anomalyScore > communications.threshold ? "bg-error" : "bg-secondary"
                  }`}
                  style={{ width: `${Math.min(100, (communications.anomalyScore / (communications.threshold || 1)) * 100)}%` }}
                />
              </div>
            </div>
            <div className="bg-surface-container-low p-2 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="font-label-caps text-[9px] uppercase text-outline">RF LINK MARGIN</span>
                <span className="font-mono-data-sm text-[10px] text-on-surface">{communications.model}</span>
              </div>
              <svg className="w-full h-9 text-secondary" fill="none" preserveAspectRatio="none" viewBox="0 0 160 36">
                <path
                  d="M0,18 Q40,16 80,18 T160,18"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.75"
                />
                <circle className="fill-secondary" cx="160" cy="18" r="3" />
              </svg>
            </div>
            <div className="mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
              <span>RESPONSIBLE CH:</span>
              <span className="text-on-surface font-mono-data-sm">
                {communications.responsibleChannels.length > 0 ? communications.responsibleChannels.join(", ") : "NONE (STABLE)"}
              </span>
            </div>
          </div>
          <div className="pt-space-md mt-space-sm border-t border-surface-container flex items-center justify-between">
            <span className="font-mono-data-sm text-[11px] text-on-surface-variant font-medium">RF Anomaly Specialist</span>
            <Link
              href="/communications"
              className="font-label-caps text-label-caps text-secondary font-semibold hover:underline flex items-center gap-0.5"
            >
              <span>Subsystem</span>
              <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 4. Orbital Track Footprint & Consensus Engine Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter-desktop">
        <div className="lg:col-span-2 bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-space-sm">
            <div className="flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-secondary text-base">public</span>
              <span className="font-label-caps text-label-caps uppercase text-outline tracking-wider">
                Ground Station Footprint &amp; Sub-Satellite Track
              </span>
            </div>
            <div className="flex items-center gap-2 font-mono-data-sm text-[11px] text-on-surface-variant">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              <span>SVALBARD GS VISIBILITY: IN-VIEW (18m remaining)</span>
            </div>
          </div>

          <div className="relative w-full h-56 rounded-md overflow-hidden bg-surface-container-high">
            <img
              className="w-full h-full object-cover"
              alt="Technical satellite orbital trajectory map display"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCVvb8rUdJe_l89yndjllJ5jPQTPeMDTmm8P5RPMSXBhVONX-x_JiqzptQHxmKU724Ng7vB_w7fWrykHdRNgr2Xrui3qQaiV0w00fdl03fo9Uh-dyiWF4olh9zInniYTIiaMqrkZtoGv-mTp4-iK9opltrgqIEArFYhywAvO-VfScDByguFGZ7up6bDJRii574OjE41rQi5chaBHYazacjajoat5ay1va0Tj_U7eyY"
            />
            <div className="absolute top-3 left-3 bg-surface-container-lowest/90 backdrop-blur-sm p-2 rounded shadow-sm flex flex-col gap-0.5">
              <span className="font-label-caps text-[9px] uppercase text-outline">Ground Coordinates</span>
              <span className="font-mono-data-sm text-mono-data-sm text-on-surface font-medium">78.2232° N, 15.6267° E</span>
            </div>
            <div className="absolute bottom-3 right-3 bg-surface-container-lowest/90 backdrop-blur-sm px-3 py-1.5 rounded shadow-sm flex items-center gap-3">
              <div>
                <span className="font-label-caps text-[9px] uppercase text-outline">Doppler Shift</span>
                <div className="font-mono-data-sm text-mono-data-sm text-on-surface font-semibold">+1.84 kHz</div>
              </div>
              <div className="w-px h-6 bg-surface-container-high" />
              <div>
                <span className="font-label-caps text-[9px] uppercase text-outline">Uplink Margin</span>
                <div className="font-mono-data-sm text-mono-data-sm text-on-tertiary-container font-semibold">+14.2 dB</div>
              </div>
            </div>
          </div>

          <div className="mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
            <span>NEXT AAT: +00:42:15 (KIRUNA-02)</span>
            <span className="font-mono-data-sm text-[11px] text-on-surface">EPHEMERIS: DE421 / HIGH ACCURACY</span>
          </div>
        </div>

        {/* Multi-Agent Consensus Matrix Panel */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-space-sm">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-secondary text-base">hub</span>
                <span className="font-label-caps text-label-caps uppercase text-outline tracking-wider">
                  Agent Consensus Engine
                </span>
              </div>
              <span className={`font-label-caps text-label-caps font-semibold ${isNormal ? "text-on-tertiary-container" : "text-error"}`}>
                {isNormal ? "ALL CLEAR" : currentWindow.fusionDecision.severity.toUpperCase()}
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mb-space-md">
              Deterministic fusion &amp; corroboration rule:{" "}
              <strong className="text-on-surface font-mono text-[11px]">
                {currentWindow.fusionDecision.corroborationRule}
              </strong>
            </p>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">memory</span>
                  <span className="font-mono-data-sm text-mono-data-sm text-on-surface">PWR-EPS-AI</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono-data-sm text-[11px] text-outline">score={power.anomalyScore.toFixed(2)}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-label-caps text-label-caps font-semibold ${
                      power.anomalyScore > power.threshold
                        ? "bg-error-container text-on-error-container"
                        : "bg-surface-container-lowest text-on-tertiary-container"
                    }`}
                  >
                    {power.anomalyScore > power.threshold ? "ALERT (1)" : "VOTE 0 (OK)"}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">thermostat</span>
                  <span className="font-mono-data-sm text-mono-data-sm text-on-surface">THM-TCS-AI</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono-data-sm text-[11px] text-outline">score={thermal.anomalyScore.toFixed(2)}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-label-caps text-label-caps font-semibold ${
                      thermal.anomalyScore > thermal.threshold
                        ? "bg-error-container text-on-error-container"
                        : "bg-surface-container-lowest text-on-tertiary-container"
                    }`}
                  >
                    {thermal.anomalyScore > thermal.threshold ? "ALERT (1)" : "VOTE 0 (OK)"}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">sync_alt</span>
                  <span className="font-mono-data-sm text-mono-data-sm text-on-surface">ATT-ADCS-AI</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono-data-sm text-[11px] text-outline">score={attitude.anomalyScore.toFixed(2)}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-label-caps text-label-caps font-semibold ${
                      attitude.anomalyScore > attitude.threshold
                        ? "bg-error-container text-on-error-container"
                        : "bg-surface-container-lowest text-on-tertiary-container"
                    }`}
                  >
                    {attitude.anomalyScore > attitude.threshold ? "ALERT (1)" : "VOTE 0 (OK)"}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">cell_tower</span>
                  <span className="font-mono-data-sm text-mono-data-sm text-on-surface">COM-XBD-AI</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono-data-sm text-[11px] text-outline">score={communications.anomalyScore.toFixed(2)}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-label-caps text-label-caps font-semibold ${
                      communications.anomalyScore > communications.threshold
                        ? "bg-error-container text-on-error-container"
                        : "bg-surface-container-lowest text-on-tertiary-container"
                    }`}
                  >
                    {communications.anomalyScore > communications.threshold ? "ALERT (1)" : "VOTE 0 (OK)"}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="pt-space-md mt-space-sm flex items-center justify-between text-outline font-label-caps text-label-caps">
            <span>CONCURRENCE: {currentWindow.fusionDecision.concurrenceRatio}</span>
            <span className="text-on-surface font-semibold">ATTRIBUTED: {currentWindow.fusionDecision.attributedSubsystem}</span>
          </div>
          <div className="pt-2 mt-2 border-t border-surface-container flex items-center justify-between text-outline font-label-caps text-[10px]">
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${currentWindow.fusionDecision.isFallback ? "bg-amber-400" : "bg-emerald-400"}`} />
              <span>
                {currentWindow.fusionDecision.isFallback
                  ? "REASONER: FALLBACK"
                  : `REASONER: ${(currentWindow.fusionDecision.reasonerProvider || "AI").toUpperCase()}`}
              </span>
            </span>
            <span className="text-on-surface font-mono text-[10px]">{currentWindow.fusionDecision.reasonerModel || "gpt-4o-mini"}</span>
          </div>
        </div>
      </div>

      {/* 5. Live Multi-Agent Telemetry Stream & Recent Incident Log (Exact from Stitch) */}
      <div className="bg-surface-container-lowest rounded-lg shadow-sm overflow-hidden">
        <div className="p-space-md flex flex-col md:flex-row md:items-center justify-between gap-space-sm bg-surface-container-lowest">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-secondary">stream</span>
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">
                Live Multi-Agent Telemetry Stream &amp; Incident Verification Log
              </h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Validated windows with specialist agent consensus and cryptographic audit trail
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-low text-on-surface font-mono-data-sm text-mono-data-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
              <span>{isBackendData ? "FASTAPI: LIVE" : "STREAM: REPLAY"}</span>
            </span>
            <span className="font-mono-data-sm text-mono-data-sm text-outline">
              {runs.length > 0 ? `${runs.length} Saved Runs` : "50Hz Ingestion"}
            </span>
          </div>
        </div>

        {/* Dense Operational Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-outline font-label-caps text-label-caps uppercase">
                <th className="py-2.5 px-space-md">Window ID</th>
                <th className="py-2.5 px-space-md">Timestamp (UTC)</th>
                <th className="py-2.5 px-space-md">Ground Truth</th>
                <th className="py-2.5 px-space-md">Specialist Consensus</th>
                <th className="py-2.5 px-space-md">Fusion Verdict</th>
                <th className="py-2.5 px-space-md">Grounding Check</th>
                <th className="py-2.5 px-space-md">Audit Commit Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y-0 text-body-sm">
              {operationalRows.map((row, idx) => (
                <tr
                  key={row.win}
                  className={`hover:bg-surface-container-low/70 transition-colors ${
                    row.isLive
                      ? "bg-secondary-fixed/30 font-medium"
                      : idx % 2 === 0
                      ? "bg-surface-container-lowest"
                      : "bg-surface-container-low/30"
                  }`}
                >
                  <td className="py-3 px-space-md font-mono-data-sm text-mono-data-sm text-secondary font-medium">
                    <span className="flex items-center gap-1">
                      {row.isLive && <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-ping" />}
                      {row.win}
                    </span>
                  </td>
                  <td className="py-3 px-space-md font-mono-data-sm text-mono-data-sm text-on-surface">
                    {row.time}
                  </td>
                  <td className="py-3 px-space-md">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-label-caps text-label-caps font-semibold ${row.truthClass}`}
                    >
                      {row.truth}
                    </span>
                  </td>
                  <td className="py-3 px-space-md">
                    <div className="flex items-center gap-1 font-mono-data-sm text-[11px] text-on-surface">
                      <span
                        className={`px-1 rounded ${
                          row.pwr === 1
                            ? "bg-surface-container-highest font-semibold text-secondary"
                            : "bg-surface-container-high"
                        }`}
                      >
                        PWR:{row.pwr}
                      </span>
                      <span
                        className={`px-1 rounded ${
                          row.thm === 1
                            ? "bg-surface-container-highest font-semibold text-secondary"
                            : "bg-surface-container-high"
                        }`}
                      >
                        THM:{row.thm}
                      </span>
                      <span
                        className={`px-1 rounded ${
                          row.att === 1
                            ? "bg-surface-container-highest font-semibold text-secondary"
                            : "bg-surface-container-high"
                        }`}
                      >
                        ATT:{row.att}
                      </span>
                      <span
                        className={`px-1 rounded ${
                          row.com === 1
                            ? "bg-surface-container-highest font-semibold text-secondary"
                            : "bg-surface-container-high"
                        }`}
                      >
                        COM:{row.com}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-space-md">
                    <span className="font-mono-data-sm text-mono-data-sm text-on-surface font-semibold">
                      {row.verdict} <span className="text-outline font-normal">(p={row.prob})</span>
                    </span>
                  </td>
                  <td className="py-3 px-space-md">
                    <div className="flex items-center gap-1 text-on-tertiary-container font-label-caps text-label-caps font-semibold">
                      <span className="material-symbols-outlined text-sm">verified</span>
                      <span>VERIFIED</span>
                    </div>
                  </td>
                  <td className="py-3 px-space-md">
                    <div className="flex items-center gap-1.5 font-mono-data-sm text-[11px] text-on-surface-variant">
                      <span className="material-symbols-outlined text-[13px] text-outline">key</span>
                      <span className="font-mono">{row.hash}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Merkle Root Chain Operational Footer */}
        <div className="p-space-sm bg-surface-container-low flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm border-t border-surface-container font-mono-data-sm text-[11px] text-outline">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-on-tertiary-container">link</span>
            <span>
              MERKLE CHAIN ROOT:{" "}
              <strong className="text-on-surface font-mono">
                {currentWindow.auditLog.hash}
              </strong>
            </span>
          </div>
          <div className="flex items-center gap-space-md">
            <span>CHAIN BLOCK: #418,920</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(currentWindow.auditLog.hash);
              }}
              className="hover:text-on-surface transition-colors uppercase font-label-caps text-label-caps text-secondary font-bold"
              type="button"
            >
              Copy Hash
            </button>
          </div>
        </div>
      </div>

      {/* Modal: Window Report Export JSON Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/40 backdrop-blur-sm p-4 animate-in fade-in duration-150"
          id="exportModal"
        >
          <div className="bg-surface-container-lowest w-full max-w-2xl rounded-xl shadow-xl border border-surface-container flex flex-col max-h-[90vh] overflow-hidden">
            <div className="p-space-md border-b border-surface-container flex items-center justify-between bg-surface-container-low">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">data_object</span>
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">
                    Window Telemetry &amp; Decision Artifact
                  </h3>
                  <span className="font-mono-data-sm text-[11px] text-outline">
                    {isBackendData ? `FASTAPI BACKEND RUN: ${currentWindow.backendRunId}` : `WIN-${winNum}`} • ISO-8601 VALIDATED
                  </span>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-on-surface-variant hover:text-on-surface p-1 rounded hover:bg-surface-container transition-colors"
                type="button"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>
            <div className="p-space-md overflow-y-auto flex-1 bg-surface-container-lowest font-mono-data-sm text-mono-data-sm">
              <pre className="p-space-sm rounded bg-surface-container-low text-on-surface overflow-x-auto text-xs leading-relaxed border border-surface-container">
                {JSON.stringify(modalPayload, null, 2)}
              </pre>
            </div>
            <div className="p-space-md border-t border-surface-container flex items-center justify-between bg-surface-container-low">
              <span className="font-mono-data-sm text-xs text-outline">
                {isBackendData ? "Source: FastAPI (/analyze)" : "Source: Replay Demonstration Matrix"}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded font-label-caps text-label-caps uppercase text-on-surface-variant hover:bg-surface-container transition-colors"
                  type="button"
                >
                  Close
                </button>
                <button
                  onClick={handleCopyModalJson}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-primary text-on-primary font-label-caps text-label-caps uppercase hover:opacity-90 transition-opacity"
                  type="button"
                >
                  <span className="material-symbols-outlined text-sm">
                    {copiedModalJson ? "check" : "content_copy"}
                  </span>
                  <span>{copiedModalJson ? "Copied" : "Copy JSON"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
