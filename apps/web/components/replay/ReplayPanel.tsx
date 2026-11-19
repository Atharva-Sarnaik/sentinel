"use client";

import React from "react";
import { useTelemetry } from "../../context/TelemetryContext";

export function ReplayPanel() {
  const {
    replayCatalog,
    replayStatus,
    selectedDataset,
    selectedSplit,
    selectedChannel,
    replaySpeedMs,
    isReplaying,
    replayError,
    setSelectedDataset,
    setSelectedSplit,
    setSelectedChannel,
    setReplaySpeedMs,
    startHistoricalReplay,
    pauseHistoricalReplay,
    resumeHistoricalReplay,
    stopHistoricalReplay,
    pauseOnAnomaly,
    togglePauseOnAnomaly,
    currentWindow,
  } = useTelemetry();

  const availableChannels =
    replayCatalog?.datasets[selectedDataset]?.channels || [];
  const activeChannelMeta = availableChannels.find(
    (c) => c.id === selectedChannel
  );

  const firstAnomalyWindow =
    activeChannelMeta && activeChannelMeta.anomaly_intervals.length > 0
      ? Math.max(0, Math.floor((activeChannelMeta.anomaly_intervals[0][0] - 50) / (replayStatus?.stride || 10)))
      : null;

  const status = replayStatus?.status || "idle";
  const isRunning = status === "running";
  const isPaused = status === "paused";
  const isCompleted = status === "completed";

  const currentWin = replayStatus?.current_window_index ?? 0;
  const totalWin = replayStatus?.total_windows ?? 0;
  const progressPct = replayStatus?.progress_percent ?? 0;
  const processedWin = replayStatus?.processed_windows ?? 0;
  const failedWin = replayStatus?.failed_windows ?? 0;
  const isGroundTruthAnomalous = replayStatus?.is_anomalous ?? false;

  // Primary signal time-series from current window
  const primarySeries = replayStatus?.latest_window?.primary_series || [];
  const hasSeries = primarySeries.length > 0;
  const minVal = hasSeries ? Math.min(...primarySeries) : -1.0;
  const maxVal = hasSeries ? Math.max(...primarySeries) : 1.0;
  const range = maxVal - minVal || 1.0;

  // Build SVG path points for the 100-step time series
  const svgWidth = 600;
  const svgHeight = 110;
  const padding = 10;
  const plotWidth = svgWidth - padding * 2;
  const plotHeight = svgHeight - padding * 2;

  const points = primarySeries.map((v, i) => {
    const x = padding + (i / Math.max(1, primarySeries.length - 1)) * plotWidth;
    const y =
      padding + plotHeight - ((v - minVal) / range) * plotHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const pathD = points.length > 0 ? `M ${points.join(" L ")}` : "";

  return (
    <div className="w-full bg-surface-container-lowest border border-surface-container rounded-lg p-space-md flex flex-col gap-space-md shadow-sm">
      {/* Top Bar: Title & Status Badges */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-surface-container pb-space-sm">
        <div className="flex items-center gap-space-sm">
          <span className="material-symbols-outlined text-secondary text-[22px]">
            history_toggle_off
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-headline-sm text-[15px] font-bold text-on-surface">
                NASA Historical Telemetry Replay Engine
              </span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold tracking-wider uppercase bg-secondary-fixed text-on-secondary-fixed">
                NASA {selectedDataset} • {selectedSplit.toUpperCase()}
              </span>
            </div>
            <p className="text-[11px] text-on-surface-variant font-mono">
              Deterministic multi-agent pipeline replay from authenticated NASA .npy repositories
            </p>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2">
          {replayError && (
            <span className="text-[11px] text-error font-mono bg-error-container/40 px-2 py-0.5 rounded border border-error/20">
              {replayError}
            </span>
          )}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-mono text-[11px] font-bold uppercase tracking-wider ${
              isRunning
                ? "bg-secondary-fixed text-on-secondary-fixed animate-pulse"
                : isPaused
                ? "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200"
                : isCompleted
                ? "bg-surface-container-high text-on-surface"
                : "bg-surface-container text-on-surface-variant"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isRunning
                  ? "bg-secondary animate-ping"
                  : isPaused
                  ? "bg-amber-500"
                  : isCompleted
                  ? "bg-emerald-500"
                  : "bg-outline"
              }`}
            />
            <span>REPLAY: {status}</span>
          </div>
        </div>
      </div>

      {/* Control Strip: Dataset, Split, Channel, Replay Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-space-md bg-surface-container-low p-space-sm rounded-md border border-surface-container">
        {/* Selectors Group */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Dataset Select */}
          <div className="flex flex-col">
            <label className="text-[10px] font-label-caps text-outline uppercase font-semibold">
              Spacecraft
            </label>
            <select
              value={selectedDataset}
              disabled={isRunning || isPaused}
              onChange={(e) => {
                const ds = e.target.value as "SMAP" | "MSL";
                setSelectedDataset(ds);
              }}
              className="bg-surface-container-lowest text-on-surface font-mono text-xs px-2 py-1 rounded border border-surface-container focus:outline-none focus:ring-1 focus:ring-secondary disabled:opacity-60 cursor-pointer"
            >
              <option value="SMAP">NASA SMAP (Soil Moisture)</option>
              <option value="MSL">NASA MSL (Curiosity Rover)</option>
            </select>
          </div>

          {/* Split Select */}
          <div className="flex flex-col">
            <label className="text-[10px] font-label-caps text-outline uppercase font-semibold">
              Split
            </label>
            <select
              value={selectedSplit}
              disabled={isRunning || isPaused}
              onChange={(e) => setSelectedSplit(e.target.value as "train" | "test")}
              className="bg-surface-container-lowest text-on-surface font-mono text-xs px-2 py-1 rounded border border-surface-container focus:outline-none focus:ring-1 focus:ring-secondary disabled:opacity-60 cursor-pointer"
            >
              <option value="test">Testing (With Anomaly Labels)</option>
              <option value="train">Training (Nominal Baseline)</option>
            </select>
          </div>

          {/* Channel Select */}
          <div className="flex flex-col">
            <label className="text-[10px] font-label-caps text-outline uppercase font-semibold">
              Channel ({availableChannels.length} available)
            </label>
            <select
              value={selectedChannel}
              disabled={isRunning || isPaused}
              onChange={(e) => setSelectedChannel(e.target.value)}
              className="bg-surface-container-lowest text-on-surface font-mono text-xs px-2 py-1 rounded border border-surface-container focus:outline-none focus:ring-1 focus:ring-secondary disabled:opacity-60 cursor-pointer max-w-[220px]"
            >
              {availableChannels.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.id} [{ch.subsystem.toUpperCase()}]
                  {ch.anomaly_count > 0 ? ` (${ch.anomaly_count} anom)` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Speed Select */}
          <div className="flex flex-col">
            <label className="text-[10px] font-label-caps text-outline uppercase font-semibold">
              Playback Interval
            </label>
            <select
              value={replaySpeedMs}
              onChange={(e) => setReplaySpeedMs(Number(e.target.value))}
              className="bg-surface-container-lowest text-on-surface font-mono text-xs px-2 py-1 rounded border border-surface-container focus:outline-none focus:ring-1 focus:ring-secondary cursor-pointer"
            >
              <option value={1000}>1.0s / window (Slow Inspection)</option>
              <option value={500}>0.5s / window (Real-time)</option>
              <option value={250}>0.25s / window (Fast Replay)</option>
              <option value={50}>50ms / window (Hyper-Speed)</option>
            </select>
          </div>
        </div>

        {/* Action Buttons & Anomaly Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Pause on Anomaly Toggle */}
          <label className="flex items-center gap-1.5 text-[11px] font-mono text-on-surface cursor-pointer select-none px-2 py-1 rounded bg-surface-container-lowest border border-surface-container">
            <input
              type="checkbox"
              checked={pauseOnAnomaly}
              onChange={(e) => togglePauseOnAnomaly(e.target.checked)}
              className="rounded text-secondary focus:ring-0 cursor-pointer"
            />
            <span className="font-semibold">Auto-Pause on Anomaly</span>
          </label>

          {/* Jump to Labeled Anomaly Button (if channel has known anomaly) */}
          {firstAnomalyWindow !== null && !isRunning && (
            <button
              onClick={() => startHistoricalReplay(firstAnomalyWindow, pauseOnAnomaly)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-error/15 text-error border border-error/30 font-label-caps text-xs font-bold uppercase hover:bg-error/25 transition-colors shadow-sm"
              type="button"
              title={`Jump directly to labeled anomaly at window ${firstAnomalyWindow}`}
            >
              <span className="material-symbols-outlined text-[16px]">crisis_alert</span>
              <span>Jump to Anomaly (W#{firstAnomalyWindow})</span>
            </button>
          )}

          {!isRunning && !isPaused && (
            <button
              onClick={() => startHistoricalReplay(0, pauseOnAnomaly)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-secondary text-on-secondary font-label-caps text-xs font-bold uppercase hover:opacity-90 transition-opacity shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">play_arrow</span>
              <span>Start Replay</span>
            </button>
          )}

          {isRunning && (
            <button
              onClick={pauseHistoricalReplay}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-amber-600 text-white font-label-caps text-xs font-bold uppercase hover:bg-amber-700 transition-colors shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">pause</span>
              <span>Pause</span>
            </button>
          )}

          {isPaused && (
            <button
              onClick={resumeHistoricalReplay}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-secondary text-on-secondary font-label-caps text-xs font-bold uppercase hover:opacity-90 transition-opacity shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">play_arrow</span>
              <span>Resume</span>
            </button>
          )}

          {(isRunning || isPaused || isCompleted) && (
            <button
              onClick={stopHistoricalReplay}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container-highest hover:bg-surface-container text-on-surface border border-surface-container font-label-caps text-xs font-bold uppercase transition-colors"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">stop</span>
              <span>Stop</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress & Live Telemetry Waveform Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
        {/* Left Column (5 cols): Metrics & Provenance */}
        <div className="lg:col-span-5 flex flex-col gap-space-sm justify-between bg-surface-container-low p-space-sm rounded-md border border-surface-container font-mono text-xs">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between items-center text-[11px] mb-1 text-on-surface-variant">
              <span>REPLAY PROGRESS</span>
              <span className="font-bold text-on-surface">
                {currentWin} / {totalWin} windows ({progressPct.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
              <div
                className="h-full bg-secondary transition-all duration-300 rounded-full"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          {/* Key Metrics Table */}
          <div className="grid grid-cols-2 gap-2 text-[11px] border-t border-surface-container pt-2">
            <div>
              <span className="text-outline block text-[9px] uppercase font-sans">Active Channel</span>
              <span className="font-bold text-on-surface">
                {selectedChannel} [{activeChannelMeta?.subsystem.toUpperCase() || "EPS"}]
              </span>
            </div>
            <div>
              <span className="text-outline block text-[9px] uppercase font-sans">NASA Ground Truth</span>
              <span
                className={`font-bold inline-flex items-center gap-1 ${
                  isGroundTruthAnomalous
                    ? "text-error font-bold animate-pulse"
                    : "text-on-tertiary-container"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isGroundTruthAnomalous ? "bg-error" : "bg-on-tertiary-container"
                  }`}
                />
                {isGroundTruthAnomalous ? "LABELED ANOMALY" : "NOMINAL REGION"}
              </span>
            </div>
            <div>
              <span className="text-outline block text-[9px] uppercase font-sans">Processed / Failed</span>
              <span className="text-on-surface">
                {processedWin} processed • {failedWin} failed
              </span>
            </div>
            <div>
              <span className="text-outline block text-[9px] uppercase font-sans">AI Reasoner Model</span>
              {(() => {
                const isFb = Boolean(
                  (replayStatus?.latest_analysis?.audit_entry?.extra?.reasoner as Record<string, unknown>)?.is_fallback ??
                    replayStatus?.latest_analysis?.audit_entry?.extra?.is_fallback ??
                    currentWindow.fusionDecision.isFallback
                );
                const rModel =
                  ((replayStatus?.latest_analysis?.audit_entry?.extra?.reasoner as Record<string, unknown>)?.model as string) ||
                  (replayStatus?.latest_analysis?.audit_entry?.extra?.model as string) ||
                  replayStatus?.latest_analysis?.explanation?.llm_model ||
                  currentWindow.fusionDecision.reasonerModel ||
                  "gpt-4o-mini";
                const fbReason =
                  ((replayStatus?.latest_analysis?.audit_entry?.extra?.reasoner as Record<string, unknown>)?.fallback_reason as string) ||
                  (replayStatus?.latest_analysis?.audit_entry?.extra?.fallback_reason as string) ||
                  currentWindow.fusionDecision.fallbackReason;

                return (
                  <div className="flex flex-col gap-0.5">
                    <span
                      className={`inline-flex items-center gap-1.5 font-semibold text-[11px] ${
                        isFb ? "text-amber-400" : "text-emerald-400"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isFb ? "bg-amber-400" : "bg-emerald-400"
                        }`}
                      />
                      {isFb ? `FALLBACK (${rModel})` : `OPENAI (${rModel})`}
                    </span>
                    {isFb && fbReason && (
                      <span
                        className="text-[9px] text-amber-300/80 truncate max-w-[190px]"
                        title={fbReason}
                      >
                        {fbReason.includes("429")
                          ? "API Quota Exceeded (429)"
                          : fbReason.includes("401")
                          ? "API Key Invalid (401)"
                          : "Fallback Safe-State Active"}
                      </span>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Active Audit Record Reference */}
          {replayStatus?.latest_analysis?.audit_entry && (
            <div className="text-[10px] bg-surface-container-lowest p-2 rounded border border-surface-container flex flex-col gap-0.5">
              <span className="text-outline uppercase text-[9px] font-sans">SQLite Ledger Hash (Task T3.1)</span>
              <span className="font-mono text-secondary truncate">
                ID: {replayStatus.latest_analysis.audit_entry.entry_id}
              </span>
              <span className="text-on-surface-variant truncate">
                Rule: {replayStatus.latest_analysis.decision.fusion_rule_applied} • Verdict:{" "}
                <span className="font-bold text-on-surface">
                  {replayStatus.latest_analysis.decision.severity.toUpperCase()}
                </span>
              </span>
            </div>
          )}
        </div>

        {/* Right Column (7 cols): Real NASA Telemetry Signal Waveform */}
        <div className="lg:col-span-7 bg-surface-container-lowest p-space-sm rounded-md border border-surface-container flex flex-col justify-between">
          <div className="flex justify-between items-center text-xs font-mono mb-1">
            <span className="font-bold text-on-surface flex items-center gap-1.5">
              <span className="material-symbols-outlined text-secondary text-[16px]">
                show_chart
              </span>
              Primary Signal Waveform [{selectedChannel} - 100 timesteps]
            </span>
            <span className="text-[10px] text-outline">
              Range: [{minVal.toFixed(3)}, {maxVal.toFixed(3)}]
            </span>
          </div>

          {hasSeries ? (
            <div className="relative w-full overflow-hidden bg-surface-container-low/40 rounded border border-surface-container-high/50 p-1">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-[110px] overflow-visible"
              >
                {/* Zero line */}
                {minVal < 0 && maxVal > 0 && (
                  <line
                    x1={padding}
                    y1={padding + plotHeight - ((0 - minVal) / range) * plotHeight}
                    x2={svgWidth - padding}
                    y2={padding + plotHeight - ((0 - minVal) / range) * plotHeight}
                    stroke="currentColor"
                    strokeDasharray="2 3"
                    className="text-surface-container-highest"
                  />
                )}
                {/* Waveform line */}
                <path
                  d={pathD}
                  fill="none"
                  stroke={isGroundTruthAnomalous ? "#dc2626" : "rgb(59 130 246)"}
                  strokeWidth="1.75"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          ) : (
            <div className="h-[110px] flex items-center justify-center text-outline font-mono text-xs border border-dashed border-surface-container rounded">
              Ready to stream telemetry. Click &quot;START REPLAY&quot; to begin.
            </div>
          )}

          <div className="flex justify-between items-center text-[10px] font-mono text-outline mt-1">
            <span>t = 0 (Window Start)</span>
            <span>t = +100s (Window End)</span>
          </div>
        </div>
      </div>

      {/* Recent Sequential History Strip (if any) */}
      {replayStatus?.recent_history && replayStatus.recent_history.length > 0 && (
        <div className="border-t border-surface-container pt-space-sm flex flex-col gap-1">
          <span className="text-[10px] font-label-caps text-outline uppercase font-semibold">
            Recent Sequential Window Evaluations (Audit Trail)
          </span>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {replayStatus.recent_history.slice(-14).map((h, i) => (
              <div
                key={h.window_id || i}
                className={`flex-shrink-0 px-2 py-1 rounded text-[10px] font-mono border flex flex-col items-center ${
                  h.severity !== "nominal"
                    ? "bg-error-container text-on-error-container border-error/30"
                    : "bg-surface-container text-on-surface border-surface-container-high"
                }`}
                title={`Window ${h.window_index}: ${h.severity} (${h.fusion_rule})`}
              >
                <span className="font-bold">W#{h.window_index}</span>
                <span className="text-[8px] uppercase tracking-tighter">{h.severity}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
