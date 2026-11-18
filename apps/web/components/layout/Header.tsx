"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetry } from "../../context/TelemetryContext";

export function Header() {
  const pathname = usePathname();
  const {
    currentWindow,
    windowIndex,
    totalWindows,
    nextWindow,
    prevWindow,
    setWindowIndex,
    exportAuditReport,
    apiStatus,
    apiHealth,
    apiError,
    refreshHealth,
    isAnalyzing,
    runAnalysis,
    resetToSimulated,
    replayCatalog,
    replayStatus,
    selectedDataset,
    selectedSplit,
    selectedChannel,
    isReplaying,
    setSelectedDataset,
    setSelectedSplit,
    setSelectedChannel,
    startHistoricalReplay,
    pauseHistoricalReplay,
    resumeHistoricalReplay,
    stopHistoricalReplay,
  } = useTelemetry();

  const [controlMode, setControlMode] = useState<"nasaReplay" | "syntheticDemo">("nasaReplay");
  const [selectedScenario, setSelectedScenario] = useState<"powerAnomaly" | "thermalAnomaly" | "nominal">("powerAnomaly");

  const navItems = [
    { label: "Mission Overview", href: "/overview" },
    { label: "Power Subsystem", href: "/power" },
    { label: "Thermal Subsystem", href: "/thermal" },
    { label: "Attitude Subsystem", href: "/attitude" },
    { label: "Communications Subsystem", href: "/communications" },
    { label: "Coordinator & Fusion Center", href: "/coordinator" },
  ];

  const isAnomalous = currentWindow.status === "ANOMALOUS";
  const isBackendLive = currentWindow.dataSource === "backend";
  const isReplayRunning = replayStatus?.status === "running";
  const isReplayPaused = replayStatus?.status === "paused";

  const availableChannels = replayCatalog?.datasets[selectedDataset]?.channels || [];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest border-b border-surface-container shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      {/* Top Bar (h-14) */}
      <div className="h-14 w-full px-margin-desktop flex items-center justify-between border-b border-surface-container">
        <div className="flex items-center gap-space-lg">
          <Link href="/overview" className="flex items-center gap-space-sm group">
            <img
              alt="SENTINEL Logo"
              className="h-8 w-auto object-contain"
              src="https://lh3.googleusercontent.com/aida/ALJJyrCuV1SHdCoDnCI5DQJW-i6sjA6HQMARmpefRh8tVcakubYR9bKac05mwSNzoiiQZ66g6zL1LUWQ-TbznkI7Bn9cTdP9ISpQhf0YyVvPlT7k96W8oVj5vC9r-Dolyc17qeaNidIe-2X8206MfW1BrKl4IsLAw7iqasadC4pAqKWLnjIDryhJCwV3JxhJWzXs_5awNZKBidLHqnKFN4vP_zXjBdXBWVrodI5oQeWa6SC3"
            />
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm font-bold tracking-tight text-on-surface leading-none">
                SENTINEL
              </span>
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">
                Orbital Telemetry OPS
              </span>
            </div>
          </Link>

          <div className="h-6 w-px bg-surface-container-high hidden md:block" />

          {/* Orbit Telemetry Badges */}
          <div className="hidden xl:flex items-center gap-space-md font-mono-data-sm text-mono-data-sm text-on-surface-variant">
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low">
              <span className="font-label-caps text-label-caps text-outline uppercase">NORAD</span>
              <span className="text-on-surface font-medium">48291</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low">
              <span className="font-label-caps text-label-caps text-outline uppercase">ORBIT</span>
              <span className="text-on-surface font-medium">LEO 540km</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container animate-pulse" />
              <span className="font-label-caps text-label-caps text-outline uppercase">LINK</span>
              <span className="text-on-surface font-medium">2.4 GHz</span>
            </div>

            {/* Real FastAPI Connection Status Pill */}
            <button
              onClick={() => refreshHealth()}
              className={`flex items-center gap-1.5 px-2 py-0.5 rounded transition-colors ${
                apiStatus === "connected"
                  ? "bg-surface-container-low text-on-tertiary-container hover:bg-surface-container"
                  : apiStatus === "connecting"
                  ? "bg-surface-container-high text-secondary"
                  : "bg-error-container text-on-error-container hover:opacity-90"
              }`}
              title={
                apiError
                  ? `API Connection Error: ${apiError}. Click to retry.`
                  : apiStatus === "connected"
                  ? `FastAPI Server Online: v${apiHealth?.version || "0.1.0"} (Tier ${apiHealth?.tier || "5"})`
                  : "Connecting to FastAPI..."
              }
              type="button"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  apiStatus === "connected"
                    ? "bg-on-tertiary-container animate-pulse"
                    : apiStatus === "connecting"
                    ? "bg-secondary animate-pulse"
                    : "bg-error"
                }`}
              />
              <span className="font-label-caps text-label-caps font-semibold uppercase">
                {apiStatus === "connected"
                  ? `API: ONLINE`
                  : apiStatus === "connecting"
                  ? "API: CONNECTING..."
                  : "API: OFFLINE"}
              </span>
            </button>
          </div>
        </div>

        {/* Right Section: MET & Lead */}
        <div className="flex items-center gap-space-lg">
          <div className="hidden sm:flex flex-col items-end">
            <span className="font-label-caps text-label-caps text-outline uppercase">Mission Elapsed Time</span>
            <span className="font-mono-data-md text-mono-data-md font-semibold text-on-surface">
              {currentWindow.met}
            </span>
          </div>

          <div className="h-6 w-px bg-surface-container-high hidden sm:block" />

          <div className="flex items-center gap-space-sm pl-space-xs">
            <div className="hidden md:flex flex-col items-end text-right">
              <span className="font-body-sm text-body-sm font-medium text-on-surface leading-tight">
                Dr. Sarah Jenkins
              </span>
              <span className="font-label-caps text-label-caps text-outline uppercase">
                Lead Flight Operations
              </span>
            </div>
            <img
              alt="Profile"
              className="w-8 h-8 rounded-full object-cover ring-1 ring-surface-container-highest"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC85pOXGirep0SwO2tFR9Qx6SPd1ErG5R8FZNysgvqBdzMznpA8uLfbr_qr-LuPLeGoQ0-8X6ay9ZUoHRV1s3S7qC5Pkq0Xn1_WhsETtN0pT_Jf6jjnwXVXcFKoo1Aw5BNFNLa7DlJ-iOiHVMziuA5sK2D6W6KPjiEhas-L-GvbxUuBzsemb4TQRjFbVc6s_mTx7RdLWN9UkW4MqoCFfvWKvrCPx_1mb9m90bgaiP0"
            />
          </div>
        </div>
      </div>

      {/* Control & Replay Bar (h-12) */}
      <div className="h-12 w-full px-margin-desktop bg-surface-container-low flex items-center justify-between border-b border-surface-container text-xs">
        <div className="flex items-center gap-space-sm overflow-x-auto py-1">
          {/* Replay Stepper */}
          <div className="flex items-center gap-1 bg-surface-container-lowest px-1.5 py-1 rounded border border-surface-container">
            <button
              onClick={prevWindow}
              disabled={windowIndex === 0 || isReplayRunning}
              className="px-1.5 py-0.5 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-mono text-[11px] transition-colors disabled:opacity-40"
              title="Previous Window"
              type="button"
            >
              &lt;
            </button>
            <span className="font-mono text-[11px] font-semibold text-on-surface px-1">
              WIN #{1000 + windowIndex} / {1000 + totalWindows - 1}
            </span>
            <button
              onClick={nextWindow}
              disabled={windowIndex === totalWindows - 1 || isReplayRunning}
              className="px-1.5 py-0.5 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-mono text-[11px] transition-colors disabled:opacity-40"
              title="Next Window"
              type="button"
            >
              &gt;
            </button>
          </div>

          {/* NASA Historical Replay Quick Selector Strip */}
          <div className="flex items-center gap-1 bg-surface-container-lowest border border-surface-container rounded p-0.5 font-mono text-[11px]">
            {/* Mode switch */}
            <select
              value={controlMode}
              onChange={(e) => setControlMode(e.target.value as "nasaReplay" | "syntheticDemo")}
              className="bg-transparent text-secondary font-bold font-sans uppercase text-[10px] px-1 py-0.5 rounded border-none focus:outline-none cursor-pointer"
            >
              <option value="nasaReplay">NASA Replay</option>
              <option value="syntheticDemo">Demo Payload</option>
            </select>

            {controlMode === "nasaReplay" ? (
              <>
                <select
                  value={selectedDataset}
                  disabled={isReplaying}
                  onChange={(e) => setSelectedDataset(e.target.value as "SMAP" | "MSL")}
                  className="bg-surface-container-low px-1.5 py-0.5 rounded text-[10px] font-bold text-on-surface border-none focus:outline-none cursor-pointer"
                >
                  <option value="SMAP">SMAP</option>
                  <option value="MSL">MSL</option>
                </select>

                <select
                  value={selectedSplit}
                  disabled={isReplaying}
                  onChange={(e) => setSelectedSplit(e.target.value as "train" | "test")}
                  className="bg-surface-container-low px-1.5 py-0.5 rounded text-[10px] font-bold text-on-surface border-none focus:outline-none cursor-pointer"
                >
                  <option value="test">TEST</option>
                  <option value="train">TRAIN</option>
                </select>

                <select
                  value={selectedChannel}
                  disabled={isReplaying}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  className="bg-surface-container-low px-1.5 py-0.5 rounded text-[10px] font-bold text-on-surface border-none focus:outline-none cursor-pointer max-w-[90px]"
                >
                  {availableChannels.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id}
                    </option>
                  ))}
                </select>

                {!isReplaying ? (
                  <button
                    onClick={() => startHistoricalReplay()}
                    className="flex items-center gap-1 px-2 py-0.5 rounded bg-secondary text-on-secondary font-sans text-[10px] font-bold uppercase hover:opacity-90"
                    type="button"
                    title="Start historical NASA telemetry replay"
                  >
                    <span className="material-symbols-outlined text-[13px]">play_arrow</span>
                    <span>Replay</span>
                  </button>
                ) : isReplayRunning ? (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={pauseHistoricalReplay}
                      className="px-1.5 py-0.5 rounded bg-amber-600 text-white font-sans text-[10px] font-bold uppercase hover:bg-amber-700"
                      type="button"
                      title="Pause replay"
                    >
                      Pause
                    </button>
                    <button
                      onClick={stopHistoricalReplay}
                      className="px-1.5 py-0.5 rounded bg-surface-container-high text-on-surface font-sans text-[10px] font-bold uppercase hover:bg-surface-container-highest"
                      type="button"
                      title="Stop replay"
                    >
                      Stop
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={resumeHistoricalReplay}
                      className="px-1.5 py-0.5 rounded bg-secondary text-on-secondary font-sans text-[10px] font-bold uppercase hover:opacity-90"
                      type="button"
                      title="Resume replay"
                    >
                      Resume
                    </button>
                    <button
                      onClick={stopHistoricalReplay}
                      className="px-1.5 py-0.5 rounded bg-surface-container-high text-on-surface font-sans text-[10px] font-bold uppercase hover:bg-surface-container-highest"
                      type="button"
                      title="Stop replay"
                    >
                      Stop
                    </button>
                  </div>
                )}
              </>
            ) : (
              <>
                <select
                  value={selectedScenario}
                  onChange={(e) =>
                    setSelectedScenario(e.target.value as "powerAnomaly" | "thermalAnomaly" | "nominal")
                  }
                  className="bg-surface-container-low px-1.5 py-0.5 rounded text-[10px] font-bold text-on-surface border-none focus:outline-none cursor-pointer"
                >
                  <option value="powerAnomaly">Power Overvoltage (P-1)</option>
                  <option value="thermalAnomaly">Thermal Runaway (T-1)</option>
                  <option value="nominal">Nominal Window (Clean)</option>
                </select>
                <button
                  onClick={() => runAnalysis(selectedScenario)}
                  disabled={isAnalyzing}
                  className="flex items-center gap-1 px-2 py-0.5 rounded bg-secondary text-on-secondary font-sans text-[10px] font-bold uppercase hover:opacity-90"
                  type="button"
                >
                  <span className={`material-symbols-outlined text-[13px] ${isAnalyzing ? "animate-spin" : ""}`}>
                    {isAnalyzing ? "sync" : "bolt"}
                  </span>
                  <span>Analyze</span>
                </button>
              </>
            )}
          </div>

          {/* Health Status Pill */}
          <div className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-lowest border border-surface-container">
            <span
              className={`w-2 h-2 rounded-full ${isAnomalous ? "bg-error animate-pulse" : "bg-on-tertiary-container"}`}
            />
            <span
              className={`font-label-caps text-label-caps font-semibold uppercase ${
                isAnomalous ? "text-error" : "text-on-surface"
              }`}
            >
              {isAnomalous ? "STATUS: ANOMALY" : "STATUS: NORMAL"}
            </span>
          </div>

          {/* Data Provenance Badge */}
          {isBackendLive ? (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-secondary-fixed text-on-secondary-fixed border border-secondary/30 font-mono text-[10px]">
              <span className="material-symbols-outlined text-[12px] text-secondary">database</span>
              <span className="font-bold uppercase">
                {replayStatus?.session_id ? `NASA-${replayStatus.dataset} REPLAY` : "FASTAPI (/analyze)"}
              </span>
              <button
                onClick={resetToSimulated}
                className="ml-1 text-[9px] underline opacity-75 hover:opacity-100 uppercase"
                title="Return to standard simulated replay"
                type="button"
              >
                Reset
              </button>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-outline font-label-caps text-label-caps">
              <span>SIMULATED REPLAY</span>
            </div>
          )}
        </div>

        {/* Right Section: Export */}
        <div className="flex items-center gap-space-sm">
          <button
            onClick={exportAuditReport}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-lowest hover:bg-surface-container text-on-surface border border-surface-container font-label-caps text-label-caps uppercase transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-[15px]">download</span>
            <span className="hidden sm:inline">Export Audit</span>
          </button>
        </div>
      </div>

      {/* Primary Subsystem Navigation Bar */}
      <div className="w-full px-margin-desktop bg-surface-container-lowest flex items-center justify-between">
        <nav className="flex items-center gap-space-lg overflow-x-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (pathname === "/" && item.href === "/overview");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`py-2.5 whitespace-nowrap transition-colors ${
                  isActive
                    ? "border-b-2 border-secondary text-on-surface font-semibold"
                    : "text-body-sm font-body-sm text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:flex items-center gap-2 text-outline font-label-caps text-label-caps">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
          <span>SECURE TELEMETRY LINK</span>
        </div>
      </div>
    </header>
  );
}
