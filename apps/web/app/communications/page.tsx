"use client";

import React, { useState } from "react";
import { useTelemetry } from "../../context/TelemetryContext";

export default function CommunicationsPage() {
  const { currentWindow } = useTelemetry();
  const comms = currentWindow.subsystems.communications;
  const [selectedChannel, setSelectedChannel] = useState<string>("all");
  const isAnomalous = comms.anomalyScore > comms.threshold || comms.severity !== "nominal";

  const c1 = comms.channels["C-1"];
  const c2 = comms.channels["C-2"];
  const d1 = comms.channels["D-1"];

  return (
    <div className="flex flex-col w-full gap-space-lg pb-12">
      {/* Subsystem Header & Status Banner */}
      <div className="flex flex-col bg-surface-container-lowest rounded-xl p-space-md shadow-sm gap-space-md">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center gap-space-sm flex-wrap">
              <span className="font-label-caps text-label-caps bg-surface-container text-outline px-2 py-0.5 rounded">
                SUBSYSTEM 05
              </span>
              <span className={`font-label-caps text-label-caps px-2 py-0.5 rounded flex items-center gap-1 ${
                isAnomalous
                  ? "bg-error-container text-on-error-container"
                  : "bg-surface-container-low text-on-tertiary-container"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  isAnomalous ? "bg-error animate-ping" : "bg-on-tertiary-container animate-pulse"
                }`} />
                {isAnomalous ? "ANOMALY DETECTED" : "NOMINAL"}
              </span>
              <span className="font-label-caps text-label-caps bg-surface-container text-secondary px-2 py-0.5 rounded">
                STATUS: {isAnomalous ? "RED / ALERT" : "GREEN / LEVEL 0"}
              </span>
              <span className="font-label-caps text-label-caps bg-surface-container-highest text-on-surface px-2 py-0.5 rounded flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">smart_toy</span>
                AGENT: {comms.model}
              </span>
            </div>
            <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight">
              Communications &amp; Data Handling Subsystem (CDHS)
            </h1>
          </div>

          {/* Quick Metrics Strip */}
          <div className="flex items-center gap-space-lg bg-surface-container-low px-space-md py-space-sm rounded-lg flex-wrap sm:flex-nowrap">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Anomaly Score</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">
                  {comms.anomalyScore.toFixed(2)}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">/ 1.00</span>
              </div>
            </div>
            <div className="w-px h-8 bg-surface-container-high hidden sm:block" />
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Threshold Limit</span>
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface">
                {comms.threshold.toFixed(2)}
              </span>
            </div>
            <div className="w-px h-8 bg-surface-container-high hidden sm:block" />
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Responsible Ch.</span>
              <span className="font-mono-data-md text-mono-data-md text-on-tertiary-container font-medium">
                {isAnomalous
                  ? comms.responsibleChannels.length > 0
                    ? comms.responsibleChannels.join(", ")
                    : "C-1 / C-2 Alert"
                  : "None (Clear)"}
              </span>
            </div>
            <div className="w-px h-8 bg-surface-container-high hidden sm:block" />
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Crypto State</span>
              <span className="font-label-caps text-label-caps bg-surface-container-lowest text-on-surface px-1.5 py-0.5 rounded flex items-center gap-1 mt-0.5">
                <span className="material-symbols-outlined text-[12px] text-secondary">verified_user</span>
                K-23 LOCK
              </span>
            </div>
          </div>
        </div>

        {/* Filter Channel Pills & Feed Selector */}
        <div className="flex items-center justify-between flex-wrap gap-space-sm pt-space-xs">
          <div className="flex items-center gap-1.5 overflow-x-auto" id="channel-tabs">
            <button
              onClick={() => setSelectedChannel("all")}
              className={`px-3 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "all"
                  ? "bg-inverse-surface text-inverse-on-surface"
                  : "bg-surface-container hover:bg-surface-container-high text-on-surface"
              }`}
              type="button"
            >
              All Channels
            </button>
            <button
              onClick={() => setSelectedChannel("c1")}
              className={`px-3 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "c1"
                  ? "bg-inverse-surface text-inverse-on-surface"
                  : "bg-surface-container hover:bg-surface-container-high text-on-surface"
              }`}
              type="button"
            >
              C-1 S-Band Uplink
            </button>
            <button
              onClick={() => setSelectedChannel("c2")}
              className={`px-3 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "c2"
                  ? "bg-inverse-surface text-inverse-on-surface"
                  : "bg-surface-container hover:bg-surface-container-high text-on-surface"
              }`}
              type="button"
            >
              C-2 X-Band Downlink
            </button>
            <button
              onClick={() => setSelectedChannel("d1")}
              className={`px-3 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "d1"
                  ? "bg-inverse-surface text-inverse-on-surface"
                  : "bg-surface-container hover:bg-surface-container-high text-on-surface"
              }`}
              type="button"
            >
              D-1 Onboard Data Bus
            </button>
          </div>
          <div className="flex items-center gap-space-md text-on-surface-variant font-mono-data-sm text-mono-data-sm">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              Sample Frequency: 100 Hz
            </span>
            <span className="hidden md:inline text-outline">|</span>
            <span className="hidden md:flex items-center gap-1 text-on-surface">
              <span className="material-symbols-outlined text-[16px] text-secondary">sync</span>
              Stream ID: 0x48A-COMM
            </span>
          </div>
        </div>
      </div>

      {/* Telemetry Overview Cards (3 Channel Breakdowns) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
        {/* C-1 Card */}
        <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between relative overflow-hidden transition-all duration-200 hover:shadow-md">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-label-caps bg-surface-container text-secondary px-1.5 py-0.5 rounded font-bold">
                  C-1
                </span>
                <span className="font-label-caps text-label-caps uppercase text-outline">S-Band Command Receiver</span>
              </div>
              <p className="font-headline-sm text-headline-sm text-on-surface mt-1">Uplink Telecommand</p>
            </div>
            <span className="font-label-caps text-label-caps bg-surface-container-low text-on-tertiary-container px-2 py-0.5 rounded font-semibold uppercase flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
              NOMINAL
            </span>
          </div>
          <div className="my-space-md grid grid-cols-2 gap-space-sm bg-surface-container-low p-space-sm rounded-lg">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Signal Level</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">
                  {c1 ? c1.currentValue.toFixed(1) : "-84.2"}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">{c1 ? c1.unit : "dBm"}</span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-tertiary-container mt-0.5 font-medium">+1.4 dB margin</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Carrier Lock</span>
              <div className="flex items-center gap-1 mt-1">
                <span className="material-symbols-outlined text-[18px] text-secondary">lock</span>
                <span className="font-mono-data-md text-mono-data-md text-on-surface font-semibold">LOCKED</span>
              </div>
              <span className="font-label-caps text-[10px] text-outline mt-1">PLL ERROR: &lt;0.04 Hz</span>
            </div>
          </div>
          <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm pt-space-xs">
            <div className="flex items-center gap-1 text-on-surface">
              <span className="font-label-caps text-label-caps text-outline uppercase">FER:</span>
              <span className="font-semibold text-on-tertiary-container">0.000%</span>
            </div>
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className="font-label-caps text-label-caps text-outline uppercase">Freq:</span>
              <span>2085.4 MHz</span>
            </div>
          </div>
          {/* Micro Sparkline SVG */}
          <div className="w-full h-8 mt-space-sm">
            <svg className="w-full h-full text-secondary" preserveAspectRatio="none" viewBox="0 0 200 32">
              <path
                d="M0,18 L20,16 L40,19 L60,17 L80,18 L100,15 L120,16 L140,17 L160,15 L180,16 L200,16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
              />
              <line stroke="currentColor" strokeDasharray="2,2" strokeOpacity="0.15" x1="0" x2="200" y1="24" y2="24" />
            </svg>
          </div>
        </div>

        {/* C-2 Card */}
        <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between relative overflow-hidden transition-all duration-200 hover:shadow-md">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-label-caps bg-surface-container text-secondary px-1.5 py-0.5 rounded font-bold">
                  C-2
                </span>
                <span className="font-label-caps text-label-caps uppercase text-outline">X-Band High-Speed Array</span>
              </div>
              <p className="font-headline-sm text-headline-sm text-on-surface mt-1">Downlink Telemetry</p>
            </div>
            <span className="font-label-caps text-label-caps bg-surface-container-low text-on-tertiary-container px-2 py-0.5 rounded font-semibold uppercase flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
              NOMINAL
            </span>
          </div>
          <div className="my-space-md grid grid-cols-2 gap-space-sm bg-surface-container-low p-space-sm rounded-lg">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Transmit Power</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">
                  {c2 ? c2.currentValue.toFixed(1) : "12.0"}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">{c2 ? c2.unit : "W"}</span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-surface-variant mt-0.5">TWTA Temp: +34.1°C</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Carrier / Noise</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">18.4</span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">dB</span>
              </div>
              <span className="font-label-caps text-[10px] text-on-tertiary-container mt-0.5">REQ: &gt;11.5 dB (PASS)</span>
            </div>
          </div>
          <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm pt-space-xs">
            <div className="flex items-center gap-1 text-on-surface">
              <span className="font-label-caps text-label-caps text-outline uppercase">Throughput:</span>
              <span className="font-semibold text-on-surface">150.0 Mbps</span>
            </div>
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className="font-label-caps text-label-caps text-outline uppercase">Modulation:</span>
              <span>OQPSK</span>
            </div>
          </div>
          {/* Micro Sparkline SVG */}
          <div className="w-full h-8 mt-space-sm">
            <svg className="w-full h-full text-secondary" preserveAspectRatio="none" viewBox="0 0 200 32">
              <path
                d="M0,14 L20,15 L40,13 L60,14 L80,12 L100,14 L120,13 L140,14 L160,13 L180,14 L200,13"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
              />
              <line stroke="currentColor" strokeDasharray="2,2" strokeOpacity="0.15" x1="0" x2="200" y1="20" y2="20" />
            </svg>
          </div>
        </div>

        {/* D-1 Card */}
        <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between relative overflow-hidden transition-all duration-200 hover:shadow-md">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-label-caps bg-surface-container text-secondary px-1.5 py-0.5 rounded font-bold">
                  D-1
                </span>
                <span className="font-label-caps text-label-caps uppercase text-outline">Internal Data Bus</span>
              </div>
              <p className="font-headline-sm text-headline-sm text-on-surface mt-1">Mil-Std-1553 Multiplex</p>
            </div>
            <span className="font-label-caps text-label-caps bg-surface-container-low text-on-tertiary-container px-2 py-0.5 rounded font-semibold uppercase flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
              NOMINAL
            </span>
          </div>
          <div className="my-space-md grid grid-cols-2 gap-space-sm bg-surface-container-low p-space-sm rounded-lg">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Bus Utilization</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">
                  {d1 ? d1.currentValue.toFixed(1) : "38.2"}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">{d1 ? d1.unit : "%"}</span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-surface-variant mt-0.5">Peak Window: 42.1%</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Buffer Margin</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">74</span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">%</span>
              </div>
              <span className="font-label-caps text-[10px] text-on-tertiary-container mt-0.5">RAM ALLOC: 512 MB</span>
            </div>
          </div>
          <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm pt-space-xs">
            <div className="flex items-center gap-1 text-on-surface">
              <span className="font-label-caps text-label-caps text-outline uppercase">CRC Errors:</span>
              <span className="font-semibold text-on-tertiary-container">0 (0.00e0)</span>
            </div>
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className="font-label-caps text-label-caps text-outline uppercase">Sync Retries:</span>
              <span>0</span>
            </div>
          </div>
          {/* Micro Sparkline SVG */}
          <div className="w-full h-8 mt-space-sm">
            <svg className="w-full h-full text-secondary" preserveAspectRatio="none" viewBox="0 0 200 32">
              <path
                d="M0,19 L20,17 L40,21 L60,18 L80,16 L100,19 L120,18 L140,16 L160,17 L180,15 L200,17"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
              />
              <line stroke="currentColor" strokeDasharray="2,2" strokeOpacity="0.15" x1="0" x2="200" y1="26" y2="26" />
            </svg>
          </div>
        </div>
      </div>

      {/* Interactive Telemetry Trends Chart */}
      <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pb-space-sm">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-secondary">show_chart</span>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Multi-Channel Telemetry Replay Track</h2>
            </div>
            <span className="font-label-caps text-label-caps text-outline uppercase mt-0.5">
              Telemetry Frames Window 1000 - {1000 + currentWindow.windowIndex} (Live Buffer Scrub)
            </span>
          </div>

          {/* Legend & Display Toggles */}
          <div className="flex items-center gap-space-md flex-wrap font-mono-data-sm text-mono-data-sm">
            <div
              className={`flex items-center gap-1.5 cursor-pointer ${selectedChannel !== "all" && selectedChannel !== "c1" ? "opacity-30" : ""}`}
              onClick={() => setSelectedChannel(selectedChannel === "c1" ? "all" : "c1")}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-secondary" />
              <span className="text-on-surface">C-1 S-Band (-dBm)</span>
            </div>
            <div
              className={`flex items-center gap-1.5 cursor-pointer ${selectedChannel !== "all" && selectedChannel !== "c2" ? "opacity-30" : ""}`}
              onClick={() => setSelectedChannel(selectedChannel === "c2" ? "all" : "c2")}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-on-tertiary-container" />
              <span className="text-on-surface">C-2 Power (W)</span>
            </div>
            <div
              className={`flex items-center gap-1.5 cursor-pointer ${selectedChannel !== "all" && selectedChannel !== "d1" ? "opacity-30" : ""}`}
              onClick={() => setSelectedChannel(selectedChannel === "d1" ? "all" : "d1")}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-inverse-surface" />
              <span className="text-on-surface">D-1 Bus Util (%)</span>
            </div>
            <div className="flex items-center gap-1 bg-surface-container px-2 py-0.5 rounded text-outline font-label-caps text-label-caps">
              <span className="w-2 h-0.5 bg-error" />
              <span>ALERT BOUNDARY</span>
            </div>
          </div>
        </div>

        {/* Chart Canvas Container */}
        <div
          className="relative w-full h-80 bg-surface-container-low rounded-lg p-space-md overflow-hidden select-none"
          id="telemetry-chart-viewport"
        >
          {/* Nominal Region Band Indicator */}
          <div className="absolute inset-x-12 top-14 bottom-14 bg-surface-container-lowest/60 pointer-events-none rounded" />
          {/* SVG Chart Line Canvas */}
          <svg className="w-full h-full overflow-visible" id="telemetry-svg" preserveAspectRatio="none" viewBox="0 0 1000 240">
            <defs>
              <linearGradient id="nominalZone" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#009668" stopOpacity="0.04" />
                <stop offset="100%" stopColor="#009668" stopOpacity="0.01" />
              </linearGradient>
            </defs>
            {/* Background Nominal Safe Corridor */}
            <rect
              fill="url(#nominalZone)"
              height="150"
              stroke="#009668"
              strokeDasharray="4,4"
              strokeOpacity="0.4"
              strokeWidth="0.75"
              width="910"
              x="50"
              y="45"
            />
            <text className="font-label-caps text-[9px] fill-on-tertiary-container opacity-80 uppercase font-semibold" x="56" y="60">
              Nominal Operating Corridor
            </text>
            {/* Alert Thresholds */}
            <line stroke="#ba1a1a" strokeDasharray="5,5" strokeOpacity="0.65" strokeWidth="1" x1="50" x2="960" y1="30" y2="30" />
            <text className="font-label-caps text-[9px] fill-error uppercase" x="965" y="33">
              U-LMT +2.0σ
            </text>
            <line stroke="#ba1a1a" strokeDasharray="5,5" strokeOpacity="0.65" strokeWidth="1" x1="50" x2="960" y1="210" y2="210" />
            <text className="font-label-caps text-[9px] fill-error uppercase" x="965" y="213">
              L-LMT -2.0σ
            </text>
            {/* Grid Lines & Labels */}
            <g stroke="#dce9ff" strokeDasharray="2,2" strokeWidth="1">
              <line x1="50" x2="960" y1="80" y2="80" />
              <line x1="50" x2="960" y1="120" y2="120" />
              <line x1="50" x2="960" y1="160" y2="160" />
              <line x1="200" x2="200" y1="20" y2="220" />
              <line x1="380" x2="380" y1="20" y2="220" />
              <line x1="560" x2="560" y1="20" y2="220" />
              <line x1="740" x2="740" y1="20" y2="220" />
              <line x1="920" x2="920" y1="20" y2="220" />
            </g>
            {/* C-1 S-Band Signal (Secondary Blue) */}
            <path
              d="M50,140 Q120,136 200,142 T380,138 T560,144 T740,136 T960,140"
              fill="none"
              id="curve-c1"
              opacity={selectedChannel === "all" || selectedChannel === "c1" ? 1 : 0.15}
              stroke="#0058be"
              strokeLinecap="round"
              strokeWidth="2"
            />
            {/* C-2 Transmit Power (Tertiary Green) */}
            <path
              d="M50,95 Q130,92 200,98 T380,94 T560,92 T740,96 T960,94"
              fill="none"
              id="curve-c2"
              opacity={selectedChannel === "all" || selectedChannel === "c2" ? 1 : 0.15}
              stroke="#009668"
              strokeLinecap="round"
              strokeWidth="2"
            />
            {/* D-1 Bus Util (Inverse Surface Charcoal) */}
            <path
              d="M50,175 Q150,170 200,180 T380,172 T560,178 T740,168 T960,174"
              fill="none"
              id="curve-d1"
              opacity={selectedChannel === "all" || selectedChannel === "d1" ? 1 : 0.15}
              stroke="#213145"
              strokeLinecap="round"
              strokeWidth="2"
            />
            {/* Current Cursor Tracking Vertical Line */}
            <line id="scrub-line" stroke="#0058be" strokeWidth="1.5" x1="740" x2="740" y1="15" y2="225" />
            <circle cx="740" cy="136" fill="#0058be" id="scrub-point-c1" r="4.5" stroke="#ffffff" strokeWidth="1.5" />
            <circle cx="740" cy="96" fill="#009668" id="scrub-point-c2" r="4.5" stroke="#ffffff" strokeWidth="1.5" />
            <circle cx="740" cy="168" fill="#213145" id="scrub-point-d1" r="4.5" stroke="#ffffff" strokeWidth="1.5" />
          </svg>
          {/* Instantaneous Readout Floating Card */}
          <div
            className="absolute top-4 right-16 bg-surface-container-lowest/95 backdrop-blur shadow-md rounded-lg p-space-sm font-mono-data-sm text-mono-data-sm w-56 pointer-events-none transition-all duration-75"
            id="plotly-hover-card"
          >
            <div className="flex items-center justify-between pb-1 border-b border-surface-container">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">
                T-Frame: {1000 + currentWindow.windowIndex}
              </span>
              <span className="text-on-surface font-semibold">14:21:48 UTC</span>
            </div>
            <div className="flex flex-col gap-1 pt-1.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-secondary font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
                  C-1 Signal
                </span>
                <span className="font-semibold text-on-surface">
                  {c1 ? c1.currentValue.toFixed(2) : "-84.18"} dBm
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-on-tertiary-container font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                  C-2 Tx Power
                </span>
                <span className="font-semibold text-on-surface">
                  {c2 ? c2.currentValue.toFixed(2) : "12.04"} W
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-inverse-surface font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-inverse-surface" />
                  D-1 Bus Util
                </span>
                <span className="font-semibold text-on-surface">
                  {d1 ? d1.currentValue.toFixed(1) : "38.4"}%
                </span>
              </div>
              <div className="mt-1 pt-1 border-t border-surface-container flex items-center justify-between text-[11px] text-outline">
                <span>Window Variance:</span>
                <span className="text-on-tertiary-container font-semibold">σ = 0.02 (Low)</span>
              </div>
            </div>
          </div>
          {/* X-Axis Timestamps Footer inside Viewport */}
          <div className="absolute bottom-2 inset-x-12 flex justify-between font-label-caps text-label-caps text-outline uppercase">
            <span>WIN #1000 [14:18:00]</span>
            <span>WIN #1010 [14:19:15]</span>
            <span>WIN #1020 [14:20:30]</span>
            <span>WIN #1030 [14:21:45]</span>
            <span>WIN #1042 [14:22:10] (HEAD)</span>
          </div>
        </div>

        {/* Chart Control Footer */}
        <div className="flex items-center justify-between flex-wrap gap-space-sm pt-space-xs text-on-surface-variant font-mono-data-sm text-mono-data-sm">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-outline">Confidence Interval:</span>
            <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-medium">99.7% (3-Sigma)</span>
            <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-medium">Kalman Smoothed</span>
          </div>
          <div className="flex items-center gap-space-sm">
            <button
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-label-caps uppercase transition-colors"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">tune</span>
              Threshold Calibration
            </button>
            <button
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-label-caps uppercase transition-colors"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">photo_camera</span>
              Export Plot
            </button>
          </div>
        </div>
      </div>

      {/* Status & Anomaly Timeline Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
        {/* Ground Station Pass Schedule (Left Column: 5 Cols) */}
        <div className="lg:col-span-5 bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-secondary">satellite_alt</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Ground Station Pass Schedule</h3>
              </div>
              <span className="font-label-caps text-label-caps bg-surface-container-low text-secondary px-2 py-0.5 rounded font-semibold uppercase">
                NEXT: SVALBARD
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Predicted tracking arcs and contact azimuths for LEO downlinks.
            </p>
          </div>

          {/* Station Pass Card: Imminent AOS */}
          <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-space-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-secondary flex items-center justify-center animate-ping" />
                <div>
                  <h4 className="font-headline-sm text-headline-sm text-on-surface">Svalbard Ground Station (SG3)</h4>
                  <span className="font-label-caps text-label-caps text-outline uppercase">
                    Coordinates: 78.229° N, 15.407° E
                  </span>
                </div>
              </div>
              <div className="flex flex-col items-end">
                <span className="font-label-caps text-label-caps text-outline uppercase">AOS Countdown</span>
                <span className="font-mono-data-lg text-mono-data-lg text-secondary font-bold">18m 24s</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 font-mono-data-sm text-mono-data-sm bg-surface-container-lowest p-2 rounded">
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Max Elevation</span>
                <span className="text-on-surface font-semibold">68.4°</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Pass Duration</span>
                <span className="text-on-surface font-semibold">09m 42s</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Carrier Plan</span>
                <span className="text-on-tertiary-container font-semibold">X-BAND 150M</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-body-sm font-body-sm pt-1">
              <span className="text-on-surface-variant">Antenna Dish 11m Tracking Config: Ready</span>
              <span className="font-label-caps text-label-caps text-on-tertiary-container font-semibold uppercase flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
                AUTOTRACK ARMED
              </span>
            </div>
          </div>

          {/* Secondary Station: In Queue */}
          <div className="p-space-sm rounded-lg bg-surface-container-lowest flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-outline text-[20px]">radar</span>
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm font-medium text-on-surface">
                  Troll Station, Antarctica (TROLL-1)
                </span>
                <span className="font-label-caps text-label-caps text-outline uppercase">
                  AOS in MET +01:42:10 | Elev 44°
                </span>
              </div>
            </div>
            <span className="font-label-caps text-label-caps bg-surface-container text-outline px-2 py-0.5 rounded uppercase">
              STANDBY
            </span>
          </div>

          {/* Hardware Transceiver State */}
          <div className="grid grid-cols-2 gap-space-sm pt-space-xs font-mono-data-sm text-mono-data-sm">
            <div className="p-2.5 rounded-lg bg-surface-container-low flex flex-col gap-0.5">
              <span className="font-label-caps text-label-caps text-outline uppercase">Transponder Unit 1 (Primary)</span>
              <span className="text-on-surface font-semibold">ACTIVE - DUPLEX</span>
              <span className="text-[11px] text-on-tertiary-container font-mono">PA Output: 40.8 dBm</span>
            </div>
            <div className="p-2.5 rounded-lg bg-surface-container-low flex flex-col gap-0.5">
              <span className="font-label-caps text-label-caps text-outline uppercase">Transponder Unit 2 (Redundant)</span>
              <span className="text-on-surface-variant font-semibold">COLD SPARE</span>
              <span className="text-[11px] text-outline font-mono">Isolation: -64 dB</span>
            </div>
          </div>
        </div>

        {/* Anomaly Timeline & Telemetry Audit Log (Right Column: 7 Cols) */}
        <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-on-tertiary-container">verified</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">CDHS Anomaly Timeline &amp; Health Log</h3>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-label-caps bg-surface-container-low text-on-tertiary-container px-2 py-0.5 rounded font-semibold uppercase">
                  0 DROPOUTS (WIN 1000 - {1000 + currentWindow.windowIndex})
                </span>
              </div>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Continuous cryptographic audit verification of telemetry and Mil-Std-1553 bus protocol frames.
            </p>
          </div>

          {/* Anomaly Window Segment Visual Bar */}
          <div className="flex flex-col gap-1.5 bg-surface-container-low p-space-sm rounded-lg">
            <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase">
              <span>Window Sweep Integrity (Frames #1000 - #{1000 + currentWindow.windowIndex})</span>
              <span className="text-on-tertiary-container font-semibold">100% CLEAN SYNCHRONIZATION</span>
            </div>
            <div className="grid grid-cols-12 gap-1 h-3 w-full">
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1000-1003: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1004-1007: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1008-1011: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1012-1015: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1016-1019: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1020-1023: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1024-1027: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1028-1031: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1032-1035: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1036-1039: Nominal" />
              <div className="bg-on-tertiary-container/80 rounded-sm" title="Frame 1040-1041: Nominal" />
              <div className="bg-secondary rounded-sm animate-pulse" title="Active Head" />
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-[11px] text-outline">
              <span>T0: 14:18:00 UTC</span>
              <span>Loss of Sync: 0s (0 frames)</span>
              <span>TN: 14:22:10 UTC</span>
            </div>
          </div>

          {/* Chronological Event Stream */}
          <div className="flex flex-col gap-2 font-mono-data-sm text-mono-data-sm">
            {/* Event 1 */}
            <div className="p-2 rounded bg-surface-container-low flex items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                <span className="text-on-surface font-semibold">14:22:10.04</span>
                <span className="font-label-caps text-label-caps bg-surface-container-lowest px-1.5 py-0.5 rounded text-secondary font-bold">
                  C-1
                </span>
                <span className="text-on-surface-variant truncate max-w-xs md:max-w-md">
                  TC Frame #48109 verified. Authenticator HMAC-SHA256 valid.
                </span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-tertiary-container font-medium shrink-0">
                BER &lt;1e-9
              </span>
            </div>
            {/* Event 2 */}
            <div className="p-2 rounded bg-surface-container-low flex items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                <span className="text-on-surface font-semibold">14:21:55.12</span>
                <span className="font-label-caps text-label-caps bg-surface-container-lowest px-1.5 py-0.5 rounded text-secondary font-bold">
                  C-2
                </span>
                <span className="text-on-surface-variant truncate max-w-xs md:max-w-md">
                  Telemetry frame sequence packet burst acknowledged by Svalbard Lead.
                </span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-surface shrink-0">150.0 Mbps</span>
            </div>
            {/* Event 3 */}
            <div className="p-2 rounded bg-surface-container-low flex items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                <span className="text-on-surface font-semibold">14:20:14.88</span>
                <span className="font-label-caps text-label-caps bg-surface-container-lowest px-1.5 py-0.5 rounded text-inverse-surface font-bold">
                  D-1
                </span>
                <span className="text-on-surface-variant truncate max-w-xs md:max-w-md">
                  1553 Bus controller completed cyclic telemetry poll cycle (RT01-RT08).
                </span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-outline shrink-0">0 CRC ERR</span>
            </div>
            {/* Event 4 */}
            <div className="p-2 rounded bg-surface-container-low flex items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                <span className="text-on-surface font-semibold">14:18:02.30</span>
                <span className="font-label-caps text-label-caps bg-surface-container-lowest px-1.5 py-0.5 rounded text-on-surface font-bold">
                  SEC
                </span>
                <span className="text-on-surface-variant truncate max-w-xs md:max-w-md">
                  Specialist RF-Anomaly-Detector recalculated score: {comms.anomalyScore.toFixed(2)} (Nominal steady).
                </span>
              </div>
              <span className="font-mono-data-sm text-[11px] text-on-tertiary-container shrink-0">
                {isAnomalous ? "ALERT" : "NOMINAL"}
              </span>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-space-xs">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px] text-outline">lock</span>
              <span className="font-mono-data-sm text-[11px] text-outline">
                Audit Hash: 9f82c...e41b9 (Signed by Lead Ops)
              </span>
            </div>
            <button
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-inverse-surface text-inverse-on-surface font-label-caps text-label-caps uppercase hover:opacity-90 transition-opacity"
              type="button"
            >
              <span className="material-symbols-outlined text-[14px]">terminal</span>
              Open Comm Console
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
