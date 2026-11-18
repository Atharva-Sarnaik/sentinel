"use client";

import React, { useState } from "react";
import { useTelemetry } from "../../context/TelemetryContext";

export default function PowerPage() {
  const { currentWindow } = useTelemetry();
  const power = currentWindow.subsystems.power;
  const [selectedChannel, setSelectedChannel] = useState<string>("all");

  const p1 = power.channels["P-1"];
  const p2 = power.channels["P-2"];
  const p3 = power.channels["P-3"];
  const p4 = power.channels["P-4"];

  const isAnom = power.severity !== "nominal";
  const score = power.anomalyScore;
  const threshold = power.threshold;
  const margin = Math.max(0, threshold - score);

  // SVG Gauge calculations
  // Arc 180 degrees from (20, 110) to (180, 110)
  // Actual score arc:
  const actualRatio = Math.min(1, Math.max(0, score / 1.0));
  const actualAngle = Math.PI - actualRatio * Math.PI;
  const actualX = 100 - 80 * Math.cos(actualAngle);
  const actualY = 110 - 80 * Math.sin(actualAngle);

  return (
    <div className="flex flex-col w-full gap-space-lg pb-12">
      {/* Subsystem Top Header & Status Banner */}
      <section className="bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
        <div className="flex flex-col sm:flex-row sm:items-center gap-space-md">
          <div className="flex items-center gap-space-sm">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-secondary">
              <span className="material-symbols-outlined text-[24px]">bolt</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-headline-md text-headline-md text-on-surface">Power Subsystem (EPS)</h1>
                <span
                  className={`px-2 py-0.5 rounded font-label-caps text-label-caps font-semibold uppercase ${
                    isAnom
                      ? "bg-error-container text-on-error-container"
                      : "bg-surface-container text-on-tertiary-container"
                  }`}
                >
                  {isAnom ? "ANOMALOUS ALERT" : "NOMINAL"}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-0.5 font-label-caps text-label-caps text-outline">
                <span>
                  SEVERITY:{" "}
                  <strong className={isAnom ? "text-error font-semibold" : "text-on-tertiary-container font-semibold"}>
                    {isAnom ? "RED / LEVEL 3" : "GREEN / LEVEL 0"}
                  </strong>
                </span>
                <span>•</span>
                <span>
                  SPECIALIST MODEL:{" "}
                  <span className="font-mono-data-sm text-on-surface font-medium">{power.model}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry Inference Readout Matrix */}
        <div className="flex flex-wrap items-center gap-space-md bg-surface-container-low px-space-md py-2 rounded-lg">
          <div className="flex flex-col">
            <span className="font-label-caps text-label-caps text-outline uppercase">Anomaly Score</span>
            <div className="flex items-baseline gap-1">
              <span className={`font-mono-data-lg text-mono-data-lg font-semibold ${isAnom ? "text-error" : "text-on-surface"}`}>
                {score.toFixed(2)}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-outline">/ 1.00</span>
            </div>
          </div>
          <div className="w-px h-8 bg-surface-container-highest" />
          <div className="flex flex-col">
            <span className="font-label-caps text-label-caps text-outline uppercase">Config Threshold</span>
            <div className="flex items-baseline gap-1">
              <span className="font-mono-data-lg text-mono-data-lg text-secondary font-semibold">
                {threshold.toFixed(2)}
              </span>
              <span className="font-label-caps text-label-caps text-outline uppercase">Z-LIMIT</span>
            </div>
          </div>
          <div className="w-px h-8 bg-surface-container-highest" />
          <div className="flex flex-col">
            <span className="font-label-caps text-label-caps text-outline uppercase">Responsible Channels</span>
            <span className={`font-mono-data-sm text-mono-data-sm font-medium mt-1 ${isAnom ? "text-error font-bold" : "text-on-tertiary-container"}`}>
              {power.responsibleChannels.length > 0 ? power.responsibleChannels.join(", ") : "None (All baseline)"}
            </span>
          </div>
          <div className="w-px h-8 bg-surface-container-highest" />

          {/* Channel Selector Pill Filters */}
          <div className="flex items-center gap-1 bg-surface-container-lowest p-1 rounded">
            {["all", "p1", "p2", "p3", "p4"].map((filter) => {
              const isActive = selectedChannel === filter;
              return (
                <button
                  key={filter}
                  onClick={() => setSelectedChannel(filter)}
                  className={`channel-filter-btn px-2.5 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                    isActive
                      ? "bg-secondary text-on-secondary font-bold"
                      : "text-on-surface-variant hover:bg-surface-container-high"
                  }`}
                  type="button"
                >
                  {filter === "all" ? "All Channels" : filter.toUpperCase().replace("P", "P-")}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Interactive Multi-Channel Comparison Chart & Real-Time Inspect Container */}
      <section className="bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pb-space-xs">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-[20px]">show_chart</span>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Time-Series Telemetry Comparison</h2>
              <span className="font-label-caps text-label-caps text-outline uppercase">
                WIN #1000 - #{1000 + currentWindow.windowIndex}
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
              Normalized feature traces against anomaly boundaries and model reconstruction variances.
            </p>
          </div>

          {/* Interactive Chart Controls & Legend */}
          <div className="flex flex-wrap items-center gap-space-md">
            <div className="flex items-center gap-space-sm text-label-caps font-label-caps">
              <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => setSelectedChannel(selectedChannel === "p1" ? "all" : "p1")}>
                <span className="w-2.5 h-2.5 rounded-sm bg-secondary" />
                <span className="text-on-surface">P-1 (Bus Voltage)</span>
              </div>
              <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => setSelectedChannel(selectedChannel === "p2" ? "all" : "p2")}>
                <span className="w-2.5 h-2.5 rounded-sm bg-inverse-surface" />
                <span className="text-on-surface">P-2 (Current)</span>
              </div>
              <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => setSelectedChannel(selectedChannel === "p3" ? "all" : "p3")}>
                <span className="w-2.5 h-2.5 rounded-sm bg-on-tertiary-container" />
                <span className="text-on-surface">P-3 (SoC %)</span>
              </div>
              <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => setSelectedChannel(selectedChannel === "p4" ? "all" : "p4")}>
                <span className="w-2.5 h-2.5 rounded-sm bg-outline" />
                <span className="text-on-surface">P-4 (Solar Array)</span>
              </div>
            </div>
            <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded">
              <button className="p-1 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface" title="Pan / Inspect" type="button">
                <span className="material-symbols-outlined text-[18px]">pan_tool</span>
              </button>
              <button className="p-1 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface" title="Box Zoom" type="button">
                <span className="material-symbols-outlined text-[18px]">zoom_in</span>
              </button>
              <button className="p-1 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface" title="Reset Axis Extents" type="button">
                <span className="material-symbols-outlined text-[18px]">restart_alt</span>
              </button>
              <button className="p-1 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface" title="Export High-Res SVG" type="button">
                <span className="material-symbols-outlined text-[18px]">photo_camera</span>
              </button>
            </div>
          </div>
        </div>

        {/* Scalable Vector Chart Canvas with Coordinate Grid */}
        <div className="relative w-full h-80 bg-surface-container-low rounded-lg overflow-hidden select-none" id="telemetry-chart-viewport">
          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 320">
            <defs>
              <pattern height="40" id="telemetry-grid" patternUnits="userSpaceOnUse" width="50">
                <path className="text-surface-container-highest" d="M 50 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeDasharray="2 2" strokeWidth="0.8" />
              </pattern>
              <linearGradient id="nominal-band-grad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#009668" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#009668" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            <rect fill="transparent" height="320" width="1000" />
            <rect fill="url(#telemetry-grid)" height="320" width="1000" />
            <rect fill="url(#nominal-band-grad)" height="200" width="1000" x="0" y="80" />

            <line stroke="#ba1a1a" strokeDasharray="4 4" strokeOpacity="0.75" strokeWidth="1.2" x1="0" x2="1000" y1="80" y2="80" />
            <text className="font-label-caps text-[10px] tracking-wider uppercase font-semibold" fill="#ba1a1a" x="12" y="74">
              CRITICAL THRESHOLD (0.70 σ)
            </text>

            {/* Trace P-1: Blue */}
            <path
              className="transition-opacity duration-200"
              d={isAnom ? "M 0 190 Q 140 192 280 188 T 560 186 T 700 120 T 840 65 T 1000 60" : "M 0 190 Q 70 185, 140 192 T 280 188 T 420 195 T 560 186 T 700 189 T 840 187 T 1000 188"}
              fill="none"
              stroke="#0058be"
              strokeWidth={selectedChannel === "p1" ? "3" : "2"}
              style={{ opacity: selectedChannel === "all" || selectedChannel === "p1" ? 1 : 0.15 }}
            />
            {/* Trace P-2: Navy */}
            <path
              className="transition-opacity duration-200"
              d="M 0 220 Q 60 215, 120 228 T 260 218 T 400 222 T 540 214 T 680 226 T 820 219 T 1000 221"
              fill="none"
              stroke="#213145"
              strokeWidth={selectedChannel === "p2" ? "3" : "2"}
              style={{ opacity: selectedChannel === "all" || selectedChannel === "p2" ? 1 : 0.15 }}
            />
            {/* Trace P-3: Teal */}
            <path
              className="transition-opacity duration-200"
              d="M 0 140 Q 80 142, 160 138 T 320 144 T 480 139 T 640 141 T 800 137 T 1000 138"
              fill="none"
              stroke="#009668"
              strokeWidth={selectedChannel === "p3" ? "3" : "2"}
              style={{ opacity: selectedChannel === "all" || selectedChannel === "p3" ? 1 : 0.15 }}
            />
            {/* Trace P-4: Slate */}
            <path
              className="transition-opacity duration-200"
              d="M 0 160 Q 90 168, 180 158 T 360 162 T 540 155 T 720 164 T 900 159 T 1000 161"
              fill="none"
              stroke="#76777d"
              strokeDasharray="3 1"
              strokeWidth={selectedChannel === "p4" ? "2.5" : "1.8"}
              style={{ opacity: selectedChannel === "all" || selectedChannel === "p4" ? 1 : 0.15 }}
            />

            <line id="scrub-crosshair" stroke="#0058be" strokeOpacity="0.8" strokeWidth="1" x1="940" x2="940" y1="0" y2="320" />
            <circle cx="940" cy={isAnom ? 60 : 188} fill="#0058be" r="4" stroke="#ffffff" strokeWidth="1.5" />
            <circle cx="940" cy="220" fill="#213145" r="4" stroke="#ffffff" strokeWidth="1.5" />
            <circle cx="940" cy="138" fill="#009668" r="4" stroke="#ffffff" strokeWidth="1.5" />
            <circle cx="940" cy="160" fill="#76777d" r="4" stroke="#ffffff" strokeWidth="1.5" />
          </svg>

          {/* Precision Readout Floating Tooltip */}
          <div className="absolute top-4 right-4 bg-surface-container-lowest p-2.5 rounded shadow-md pointer-events-none flex flex-col gap-1 w-52 border border-surface-container">
            <div className="flex items-center justify-between pb-1">
              <span className="font-label-caps text-label-caps text-outline uppercase">
                WINDOW #{1000 + currentWindow.windowIndex}
              </span>
              <span className={`font-label-caps text-label-caps font-semibold uppercase ${isAnom ? "text-error" : "text-on-tertiary-container"}`}>
                {isAnom ? "ALERT" : "NOMINAL"}
              </span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-secondary font-medium">P-1 Bus:</span>
              <span className="text-on-surface font-semibold">{p1?.currentValue.toFixed(2)} V</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-inverse-surface font-medium">P-2 Curr:</span>
              <span className="text-on-surface font-semibold">{p2?.currentValue.toFixed(2)} A</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-on-tertiary-container font-medium">P-3 SoC:</span>
              <span className="text-on-surface font-semibold">{p3?.currentValue.toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline font-medium">P-4 Array:</span>
              <span className="text-on-surface font-semibold">{p4?.currentValue.toFixed(1)} W</span>
            </div>
          </div>

          {/* Dual Y-Axis Labels */}
          <div className="absolute left-2 top-2 flex flex-col justify-between h-[90%] font-mono-data-sm text-[10px] text-outline pointer-events-none">
            <span>+1.00 σ</span>
            <span className="text-error font-medium">0.70 LIMIT</span>
            <span>+0.35 σ</span>
            <span>0.00 BASE</span>
            <span>-0.50 σ</span>
          </div>

          {/* X-Axis Window Markings */}
          <div className="absolute bottom-1.5 left-14 right-4 flex justify-between font-mono-data-sm text-[10px] text-outline pointer-events-none">
            <span>WIN 1000</span>
            <span>WIN 1010</span>
            <span>WIN 1020</span>
            <span>WIN 1030</span>
            <span className="text-secondary font-bold">WIN #{1000 + currentWindow.windowIndex} (LIVE)</span>
          </div>
        </div>
      </section>

      {/* Detailed Channel Breakdown Cards (4 Columns for P-1, P-2, P-3, P-4) */}
      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-space-md">
        {/* Channel P-1 */}
        <div
          className={`bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between transition-opacity ${
            selectedChannel === "all" || selectedChannel === "p1" ? "opacity-100" : "opacity-30"
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-secondary" />
                <span className="font-label-caps text-label-caps text-outline uppercase">CHANNEL P-1</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded font-label-caps text-label-caps font-semibold uppercase ${
                  isAnom ? "bg-error-container text-on-error-container" : "bg-surface-container text-on-tertiary-container"
                }`}
              >
                {isAnom ? "OUT OF BOUNDS" : "NOMINAL"}
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-1">Regulated Bus Voltage</div>
            <div className="mt-space-md flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold tracking-tight">
                {p1?.currentValue.toFixed(2)}
              </span>
              <span className="font-body-sm text-body-sm text-outline font-medium">V</span>
            </div>
          </div>
          <div className="mt-space-md pt-space-sm bg-surface-container-low p-2 rounded flex flex-col gap-1.5">
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">Mean Baseline:</span>
              <span className="text-on-surface font-medium">{p1?.baseline}</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">StdDev (σ):</span>
              <span className="text-on-surface font-medium">0.08 V</span>
            </div>
            <div className="h-6 w-full mt-1">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 120 24">
                <path d="M 0 14 L 20 12 L 40 15 L 60 10 L 80 13 L 100 11 L 120 12" fill="none" stroke="#0058be" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </div>

        {/* Channel P-2 */}
        <div
          className={`bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between transition-opacity ${
            selectedChannel === "all" || selectedChannel === "p2" ? "opacity-100" : "opacity-30"
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-inverse-surface" />
                <span className="font-label-caps text-label-caps text-outline uppercase">CHANNEL P-2</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-surface-container font-label-caps text-label-caps text-on-tertiary-container font-semibold uppercase">
                NOMINAL
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-1">Total System Load Current</div>
            <div className="mt-space-md flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold tracking-tight">
                {p2?.currentValue.toFixed(2)}
              </span>
              <span className="font-body-sm text-body-sm text-outline font-medium">A</span>
            </div>
          </div>
          <div className="mt-space-md pt-space-sm bg-surface-container-low p-2 rounded flex flex-col gap-1.5">
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">Mean Baseline:</span>
              <span className="text-on-surface font-medium">{p2?.baseline}</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">StdDev (σ):</span>
              <span className="text-on-surface font-medium">0.12 A</span>
            </div>
            <div className="h-6 w-full mt-1">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 120 24">
                <path d="M 0 12 L 20 16 L 40 10 L 60 14 L 80 12 L 100 13 L 120 11" fill="none" stroke="#213145" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </div>

        {/* Channel P-3 */}
        <div
          className={`bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between transition-opacity ${
            selectedChannel === "all" || selectedChannel === "p3" ? "opacity-100" : "opacity-30"
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-on-tertiary-container" />
                <span className="font-label-caps text-label-caps text-outline uppercase">CHANNEL P-3</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-surface-container font-label-caps text-label-caps text-on-tertiary-container font-semibold uppercase">
                NOMINAL
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-1">Battery State of Charge</div>
            <div className="mt-space-md flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold tracking-tight">
                {p3?.currentValue.toFixed(1)}
              </span>
              <span className="font-body-sm text-body-sm text-outline font-medium">%</span>
            </div>
          </div>
          <div className="mt-space-md pt-space-sm bg-surface-container-low p-2 rounded flex flex-col gap-1.5">
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">Mean Baseline:</span>
              <span className="text-on-surface font-medium">{p3?.baseline}</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">StdDev (σ):</span>
              <span className="text-on-surface font-medium">0.05%</span>
            </div>
            <div className="h-6 w-full mt-1">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 120 24">
                <path d="M 0 16 L 20 14 L 40 12 L 60 11 L 80 10 L 100 9 L 120 8" fill="none" stroke="#009668" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </div>

        {/* Channel P-4 */}
        <div
          className={`bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between transition-opacity ${
            selectedChannel === "all" || selectedChannel === "p4" ? "opacity-100" : "opacity-30"
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-outline" />
                <span className="font-label-caps text-label-caps text-outline uppercase">CHANNEL P-4</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-surface-container font-label-caps text-label-caps text-on-tertiary-container font-semibold uppercase">
                NOMINAL
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-1">Solar Array Output Combined</div>
            <div className="mt-space-md flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold tracking-tight">
                {p4?.currentValue.toFixed(1)}
              </span>
              <span className="font-body-sm text-body-sm text-outline font-medium">W</span>
            </div>
          </div>
          <div className="mt-space-md pt-space-sm bg-surface-container-low p-2 rounded flex flex-col gap-1.5">
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">Mean Baseline:</span>
              <span className="text-on-surface font-medium">{p4?.baseline}</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-outline">StdDev (σ):</span>
              <span className="text-on-surface font-medium">2.40 W</span>
            </div>
            <div className="h-6 w-full mt-1">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 120 24">
                <path d="M 0 15 L 20 11 L 40 14 L 60 9 L 80 12 L 100 10 L 120 8" fill="none" stroke="#76777d" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* Specialist Anomaly Detection & Feature Contribution Split View (Exact from Stitch) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
        {/* Feature Importance & Reconstruction Error per Channel (Col 8) */}
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-space-sm">
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">
                  Autoencoder Reconstruction Error &amp; Feature Contribution
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Loss per telemetry vector in Window #{1000 + currentWindow.windowIndex} against baseline distribution model.
                </p>
              </div>
              <span className="font-mono-data-sm text-mono-data-sm px-2 py-0.5 rounded bg-surface-container-low text-on-surface">
                Loss: {isAnom ? "0.0812 MSE" : "0.0034 MSE"}
              </span>
            </div>

            {/* Relative Bar Distribution Visualizer */}
            <div className="mt-space-md flex flex-col gap-space-md">
              {/* Channel P-1 Bar */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center font-mono-data-sm text-mono-data-sm">
                  <span className="font-semibold text-secondary">P-1 (EPS-BUS-V)</span>
                  <span className="text-on-surface">
                    {isAnom ? "0.078 MSE (58% contrib)" : "0.038 MSE (28% contrib)"}
                  </span>
                </div>
                <div className="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isAnom ? "bg-error" : "bg-secondary"}`}
                    style={{ width: isAnom ? "58%" : "28%" }}
                  />
                </div>
              </div>

              {/* Channel P-2 Bar */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center font-mono-data-sm text-mono-data-sm">
                  <span className="font-semibold text-inverse-surface">P-2 (SYS-LOAD-I)</span>
                  <span className="text-on-surface">0.046 MSE (34% contrib)</span>
                </div>
                <div className="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
                  <div className="h-full bg-inverse-surface rounded-full" style={{ width: "34%" }} />
                </div>
              </div>

              {/* Channel P-3 Bar */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center font-mono-data-sm text-mono-data-sm">
                  <span className="font-semibold text-on-tertiary-container">P-3 (BATT-SOC)</span>
                  <span className="text-on-surface">0.016 MSE (12% contrib)</span>
                </div>
                <div className="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
                  <div className="h-full bg-on-tertiary-container rounded-full" style={{ width: "12%" }} />
                </div>
              </div>

              {/* Channel P-4 Bar */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center font-mono-data-sm text-mono-data-sm">
                  <span className="font-semibold text-outline">P-4 (SOLAR-ARRAY-P)</span>
                  <span className="text-on-surface">0.035 MSE (26% contrib)</span>
                </div>
                <div className="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
                  <div className="h-full bg-outline rounded-full" style={{ width: "26%" }} />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-space-lg pt-space-sm flex items-center justify-between font-label-caps text-label-caps text-outline">
            <span>ENCODER LATENT DIM: 16</span>
            <span>LATENCY: 4.8ms</span>
            <span className={isAnom ? "text-error font-semibold" : "text-on-tertiary-container"}>
              DRIFT CONFIDENCE: {isAnom ? "ANOMALOUS EXCURSION" : "99.8% NOMINAL"}
            </span>
          </div>
        </div>

        {/* Threshold vs Actual Anomaly Score Gauge & Radial Instrumentation (Col 4) */}
        <div className="lg:col-span-4 bg-surface-container-lowest rounded-lg p-space-md shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-space-sm">
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Anomaly Gauge</h3>
              <span className="font-label-caps text-label-caps text-outline uppercase">ENSEMBLE DETECTOR</span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Combined statistical distance &amp; manifold reconstruction.
            </p>

            {/* Circular Arc Visualizer (SVG Gauge) */}
            <div className="relative flex items-center justify-center my-space-md">
              <svg className="w-48 h-32" viewBox="0 0 200 120">
                {/* Background Arc */}
                <path d="M 20 110 A 80 80 0 0 1 180 110" fill="none" stroke="#e5eeff" strokeLinecap="round" strokeWidth="14" />
                {/* Threshold Marker Line at 70% of arc */}
                <line stroke="#ba1a1a" strokeLinecap="round" strokeWidth="3" x1="145" x2="152" y1="36" y2="28" />
                {/* Actual Value Arc */}
                <path
                  d={`M 20 110 A 80 80 0 0 1 ${actualX.toFixed(1)} ${actualY.toFixed(1)}`}
                  fill="none"
                  stroke={isAnom ? "#ba1a1a" : "#009668"}
                  strokeLinecap="round"
                  strokeWidth="14"
                />
              </svg>
              {/* Gauge Readout In Center Base */}
              <div className="absolute bottom-0 flex flex-col items-center">
                <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface leading-none">
                  {score.toFixed(2)}
                </span>
                <span className={`font-label-caps text-label-caps font-semibold uppercase mt-0.5 ${isAnom ? "text-error" : "text-on-tertiary-container"}`}>
                  {isAnom ? `ALERT (${score.toFixed(2)} / ${threshold.toFixed(2)})` : `NOMINAL (${score.toFixed(2)} / ${threshold.toFixed(2)})`}
                </span>
              </div>
            </div>
          </div>

          {/* Anomaly Threshold Reference Table */}
          <div className="bg-surface-container-low p-2.5 rounded flex flex-col gap-1.5 font-mono-data-sm text-mono-data-sm">
            <div className="flex items-center justify-between">
              <span className="text-outline">Current Window:</span>
              <span className={`font-semibold ${isAnom ? "text-error" : "text-on-surface"}`}>{score.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-outline">Alert Threshold:</span>
              <span className="text-error font-semibold">{threshold.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-outline">Delta to Tripwire:</span>
              <span className={`font-semibold ${isAnom ? "text-error" : "text-on-tertiary-container"}`}>
                {isAnom ? `-${(score - threshold).toFixed(2)} trip` : `+${margin.toFixed(2)} margin`}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
