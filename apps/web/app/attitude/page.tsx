"use client";

import React, { useState } from "react";
import { useTelemetry } from "../../context/TelemetryContext";

export default function AttitudePage() {
  const { currentWindow } = useTelemetry();
  const attitude = currentWindow.subsystems.attitude;
  const [selectedChannel, setSelectedChannel] = useState<string>("all");

  const a1 = attitude.channels["A-1"];
  const a2 = attitude.channels["A-2"];
  const a3 = attitude.channels["A-3"];
  const a4 = attitude.channels["A-4"];

  const isAnom = attitude.severity !== "nominal";
  const winNum = 1000 + currentWindow.windowIndex;

  return (
    <div className="flex flex-col w-full gap-space-lg pb-12">
      {/* Subsystem Header Bar */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md p-space-md rounded bg-surface-container-lowest shadow-sm">
        <div className="flex flex-col gap-space-xs">
          <div className="flex flex-wrap items-center gap-space-sm">
            <h1 className="font-headline-md text-headline-md text-on-surface">
              Attitude Determination &amp; Control Subsystem (ADCS)
            </h1>
            <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded font-label-caps text-label-caps uppercase ${isAnom ? "bg-error-container text-on-error-container" : "bg-tertiary-fixed text-on-tertiary-fixed"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isAnom ? "bg-error animate-pulse" : "bg-on-tertiary-fixed-variant animate-pulse"}`} />
              <span>{isAnom ? "POINTING ANOMALY" : "Nominal"}</span>
            </div>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-caps text-label-caps uppercase">
              <span>Severity: {isAnom ? "Red / Level 2" : "Green / Level 0"}</span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-space-md gap-y-1 font-mono-data-sm text-mono-data-sm text-on-surface-variant">
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase mr-1">Specialist Model:</span>
              <span className="text-on-surface font-medium">{attitude.model}</span>
            </div>
            <div className="hidden sm:inline text-outline-variant">/</div>
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase mr-1">Pointing Error:</span>
              <span className="text-on-surface font-semibold">&lt; 0.02°</span> (Enclosure lock target: Earth-Nadir)
            </div>
          </div>
        </div>

        {/* Anomaly Score Gauges & Channels Filter */}
        <div className="flex flex-wrap items-center gap-space-md">
          <div className="flex items-center gap-space-md px-space-md py-1.5 rounded bg-surface-container-low">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Anomaly Score</span>
              <div className="flex items-baseline gap-1">
                <span className={`font-mono-data-lg text-mono-data-lg font-bold leading-none ${isAnom ? "text-error" : "text-on-surface"}`}>
                  {attitude.anomalyScore.toFixed(2)}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">
                  / {attitude.threshold.toFixed(2)} LIM
                </span>
              </div>
            </div>
            <div className="w-20 h-2 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${isAnom ? "bg-error" : "bg-secondary"}`}
                style={{ width: `${Math.min(100, (attitude.anomalyScore / 0.75) * 100)}%` }}
              />
            </div>
          </div>

          {/* Channel Toggle Pills */}
          <div className="flex items-center p-0.5 rounded bg-surface-container" id="channelPillGroup">
            {["all", "a1", "a2", "a3", "a4"].map((filter) => {
              const isActive = selectedChannel === filter;
              return (
                <button
                  key={filter}
                  onClick={() => setSelectedChannel(filter)}
                  className={`channel-pill px-2.5 py-1 rounded font-label-caps text-label-caps uppercase transition-colors ${
                    isActive
                      ? "bg-surface-container-lowest text-on-surface shadow-sm font-semibold"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                  type="button"
                >
                  {filter === "all" ? "All Channels" : filter.toUpperCase().replace("A", "A-")}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Telemetry Graph + Context Visual Strip */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-lg">
        {/* Main SVG Time Series Graph (Col 8) */}
        <div className="xl:col-span-8 flex flex-col p-space-md rounded bg-surface-container-lowest shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-space-sm pb-space-sm mb-space-sm">
            <div className="flex items-center gap-space-sm">
              <span className="font-headline-sm text-headline-sm text-on-surface">Normalized Angular Rate &amp; Reaction Torque</span>
              <span className="font-mono-data-sm text-mono-data-sm text-on-surface-variant px-2 py-0.5 rounded bg-surface-container-low">CH: A-1 ... A-4</span>
            </div>
            <div className="flex items-center gap-space-md font-label-caps text-label-caps flex-wrap">
              <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-secondary" /><span className="text-on-surface-variant">A-1 (Pitch)</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-secondary-container" /><span className="text-on-surface-variant">A-2 (Roll)</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-on-tertiary-container" /><span className="text-on-surface-variant">A-3 (Yaw/RWA)</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-inverse-primary" /><span className="text-on-surface-variant">A-4 (Tracker)</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-error border-b border-dashed border-error" /><span className="text-error">Upper Bound (0.75)</span></div>
            </div>
          </div>

          {/* Graph Stage */}
          <div className="relative w-full h-72 sm:h-80 bg-surface-container-low rounded p-2 overflow-hidden select-none" id="chartCanvasContainer">
            <svg className="w-full h-full text-outline-variant" preserveAspectRatio="none" viewBox="0 0 900 300">
              {/* Background Grid lines */}
              <line className="opacity-40" stroke="currentColor" strokeDasharray="4,4" strokeWidth="0.7" x1="60" x2="880" y1="30" y2="30" />
              <line className="opacity-40" stroke="currentColor" strokeDasharray="4,4" strokeWidth="0.7" x1="60" x2="880" y1="90" y2="90" />
              <line className="opacity-40" stroke="currentColor" strokeDasharray="4,4" strokeWidth="0.7" x1="60" x2="880" y1="150" y2="150" />
              <line className="opacity-40" stroke="currentColor" strokeDasharray="4,4" strokeWidth="0.7" x1="60" x2="880" y1="210" y2="210" />
              <line className="opacity-80" stroke="currentColor" strokeWidth="1" x1="60" x2="880" y1="270" y2="270" />

              {/* Vertical Guides */}
              <line className="opacity-25" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="160" x2="160" y1="20" y2="270" />
              <line className="opacity-25" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="340" x2="340" y1="20" y2="270" />
              <line className="opacity-25" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="520" x2="520" y1="20" y2="270" />
              <line className="opacity-25" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="700" x2="700" y1="20" y2="270" />
              <line className="opacity-25" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="880" x2="880" y1="20" y2="270" />

              {/* Upper Anomaly Boundary line */}
              <line className="opacity-80" stroke="#ba1a1a" strokeDasharray="6,4" strokeWidth="1.5" x1="60" x2="880" y1="65" y2="65" />
              <text className="font-label-caps text-[9px] font-bold" fill="#ba1a1a" x="815" y="60">THRESHOLD 0.75</text>
              <line className="opacity-30" stroke="currentColor" strokeWidth="1" x1="60" x2="880" y1="230" y2="230" />

              {/* Channel A-1 Line */}
              {(selectedChannel === "all" || selectedChannel === "a1") && (
                <path
                  d={isAnom ? "M 60 210 Q 260 212 460 208 T 660 120 T 760 55 T 880 50" : "M 60 210 Q 110 200, 160 205 T 260 212 T 360 204 T 460 208 T 560 202 T 660 206 T 760 201 T 880 203"}
                  fill="none"
                  stroke="#0058be"
                  strokeWidth={selectedChannel === "a1" || isAnom ? "2.5" : "2"}
                />
              )}

              {/* Channel A-2 Line */}
              {(selectedChannel === "all" || selectedChannel === "a2") && (
                <path
                  d="M 60 218 L 110 214 L 160 217 L 220 212 L 280 215 L 340 211 L 410 216 L 480 213 L 550 217 L 620 212 L 690 215 L 770 210 L 830 214 L 880 211"
                  fill="none"
                  stroke="#2170e4"
                  strokeLinejoin="round"
                  strokeWidth="1.7"
                />
              )}

              {/* Channel A-3 Line */}
              {(selectedChannel === "all" || selectedChannel === "a3") && (
                <path
                  d="M 60 236 Q 140 232, 220 235 T 380 233 T 540 234 T 700 231 T 880 233"
                  fill="none"
                  stroke="#009668"
                  strokeWidth="1.5"
                />
              )}

              {/* Channel A-4 Line */}
              {(selectedChannel === "all" || selectedChannel === "a4") && (
                <path
                  d="M 60 248 L 120 246 L 180 247 L 240 245 L 310 247 L 390 244 L 470 247 L 550 245 L 630 246 L 710 244 L 790 246 L 880 244"
                  fill="none"
                  stroke="#76777d"
                  strokeDasharray="3,3"
                  strokeWidth="1.2"
                />
              )}

              {/* Interactive Vertical Scrubber Line */}
              <line stroke="#0058be" strokeDasharray="2,2" strokeWidth="1.5" x1="750" x2="750" y1="20" y2="270" />
              <circle cx="750" cy={isAnom ? 55 : 201} fill="#0058be" r="3.5" />
              <circle cx="750" cy="211" fill="#2170e4" r="3" />

              {/* Y-Axis Ticks */}
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="20" y="34">0.90</text>
              <text className="font-mono-data-sm text-[10px] font-semibold" fill="#ba1a1a" x="20" y="69">0.75</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="20" y="94">0.60</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="20" y="154">0.40</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="20" y="214">0.20</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="20" y="274">0.00</text>

              {/* X-Axis Labels */}
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="60" y="290">WIN #1000</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="250" y="290">WIN #1010</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="450" y="290">WIN #1020</text>
              <text className="font-mono-data-sm text-[10px]" fill="#45464d" x="650" y="290">WIN #1030</text>
              <text className="font-mono-data-sm text-[10px] font-semibold" fill="#0058be" x="825" y="290">
                WIN #{winNum} (NOW)
              </text>
            </svg>

            {/* Floating Readout Tooltip */}
            <div className="absolute top-4 right-4 bg-surface-container-lowest p-space-sm rounded shadow-md pointer-events-none flex flex-col gap-0.5 border border-surface-container">
              <div className="flex items-center justify-between gap-space-md">
                <span className="font-label-caps text-label-caps text-outline uppercase">Active Window</span>
                <span className="font-mono-data-sm text-mono-data-sm font-bold text-on-surface">#{winNum}</span>
              </div>
              <div className="flex items-center justify-between gap-space-md font-mono-data-sm text-mono-data-sm">
                <span className="text-secondary font-medium">A-1 (Pitch):</span>
                <span className="text-on-surface">0.0042 rad/s</span>
              </div>
              <div className="flex items-center justify-between gap-space-md font-mono-data-sm text-mono-data-sm">
                <span className="text-secondary-container font-medium">A-2 (Roll):</span>
                <span className="text-on-surface">0.0039 rad/s</span>
              </div>
              <div className="flex items-center justify-between gap-space-md font-mono-data-sm text-mono-data-sm">
                <span className="text-on-tertiary-container font-medium">A-3 (Yaw):</span>
                <span className="text-on-surface">0.0011 rad/s</span>
              </div>
              <div className="flex items-center justify-between gap-space-md font-mono-data-sm text-mono-data-sm">
                <span className="text-outline font-medium">A-4 (Confidence):</span>
                <span className="text-on-surface">99.8%</span>
              </div>
              <div className="mt-1 pt-1 border-t border-surface-container flex items-center justify-between gap-space-md font-label-caps text-label-caps">
                <span className="text-outline uppercase">Threshold Status</span>
                <span className={isAnom ? "text-error uppercase font-semibold" : "text-on-tertiary-container uppercase font-semibold"}>
                  {isAnom ? "Tripwire Exceeded (+12%)" : "In Bounds (-74%)"}
                </span>
              </div>
            </div>
          </div>

          {/* Time Range Slider Control Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-sm mt-space-sm pt-space-xs px-1">
            <div className="flex items-center gap-space-sm font-mono-data-sm text-mono-data-sm text-on-surface-variant">
              <span className="font-label-caps text-label-caps text-outline uppercase">Historical Buffer:</span>
              <span className="px-1.5 py-0.5 rounded bg-surface-container text-on-surface font-semibold">
                42 Telemetry Frames (35m 10s)
              </span>
            </div>
            <div className="flex items-center gap-space-sm w-full sm:w-auto">
              <span className="font-label-caps text-label-caps text-outline uppercase whitespace-nowrap">Scrub Span</span>
              <input
                className="w-full sm:w-56 h-1.5 bg-surface-container-high rounded cursor-pointer accent-secondary"
                max="1042"
                min="1000"
                type="range"
                value={winNum}
                readOnly
              />
              <button
                className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-caps text-label-caps uppercase hover:bg-surface-container-high transition-colors"
                type="button"
              >
                Snap Live
              </button>
            </div>
          </div>
        </div>

        {/* Subsystem Visual Context Panel: Vector & Spacecraft Telemetry (Col 4) */}
        <div className="xl:col-span-4 flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm">
          <div className="flex flex-col gap-space-sm">
            <div className="flex items-center justify-between">
              <span className="font-headline-sm text-headline-sm text-on-surface">Vector Orientation</span>
              <span className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-surface-container text-on-surface uppercase font-medium">
                Nadir Lock 3-Axis
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Star trackers ST-1 and ST-2 maintain continuous boresight fix on guide stars with zero ephemeris drift detected.
            </p>

            {/* Synthetic Orbit Orientation Card with visual asset from Stitch */}
            <div className="relative w-full h-44 rounded overflow-hidden mt-space-xs flex items-center justify-center bg-inverse-surface">
              <img
                className="w-full h-full object-cover opacity-60"
                alt="Technical orthographic diagram of an Earth-observing satellite in low earth orbit with attitude reference vectors."
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCgzYbR4bNzPLm0vVTmMMbDa9sTwBUXLeTQNNN8gPvuRdTmxf27XbPpk71r8diZaBD4uEE5O7Gj0kVd7gFTQOC8BEIJlEXXu4sTpakdoQywydnOa7ycqh_jz6X6YZ7Ikip9tet-fl36WTh822iAZBr_h4RmaXAiVe8fjfqF-ZvYVGYcUVXbczVpcf8hBc8lPxps49mFPdgSA_N1zMsRDkeMnQDne8CqFNi8d3_NNc4"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-inverse-surface via-transparent to-transparent" />
              <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between px-2.5 py-1.5 rounded bg-inverse-surface/90 text-inverse-on-surface font-mono-data-sm text-mono-data-sm">
                <div>
                  <span className="font-label-caps text-label-caps text-primary-fixed uppercase block text-[9px]">QUATERNION [Q0..Q3]</span>
                  <span>0.7071, 0.0012, -0.0008, 0.7071</span>
                </div>
                <div className="text-right">
                  <span className="font-label-caps text-label-caps text-primary-fixed uppercase block text-[9px]">SLEW ACCEL</span>
                  <span>0.000°/s²</span>
                </div>
              </div>
            </div>
          </div>

          {/* Pointing Budget Breakdown mini-table */}
          <div className="flex flex-col gap-1.5 mt-space-md pt-space-sm border-t border-surface-container">
            <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase">
              <span>Error Source</span>
              <span>Allocated</span>
              <span>Actual</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-on-surface">Star Tracker Ephemeris</span>
              <span className="text-on-surface-variant">0.010°</span>
              <span className="text-on-tertiary-container font-semibold">0.003°</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-on-surface">RWA Micro-vibration</span>
              <span className="text-on-surface-variant">0.008°</span>
              <span className="text-on-tertiary-container font-semibold">0.002°</span>
            </div>
            <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
              <span className="text-on-surface">Structural Thermal Warp</span>
              <span className="text-on-surface-variant">0.015°</span>
              <span className="text-on-tertiary-container font-semibold">0.006°</span>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Channel Metrics Grid (4 Cards: A-1, A-2, A-3, A-4) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-space-lg">
        {/* Channel A-1 */}
        <div className="flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              <span className="font-label-caps text-label-caps text-outline uppercase">Channel A-1</span>
            </div>
            <span className={`px-2 py-0.5 rounded font-label-caps text-label-caps uppercase font-semibold ${isAnom ? "bg-error-container text-on-error-container" : "bg-tertiary-fixed text-on-tertiary-fixed"}`}>
              {isAnom ? "Alert" : "Nominal"}
            </span>
          </div>
          <div className="my-space-md">
            <span className="font-body-sm text-body-sm text-on-surface-variant block mb-1">Pitch Axis Angular Rate</span>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                {a1 ? a1.currentValue.toFixed(4) : "0.0042"}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-outline">rad/s</span>
            </div>
          </div>
          <div className="pt-space-sm border-t border-surface-container flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <span className="text-on-surface-variant font-label-caps text-label-caps uppercase">Baseline Dev.</span>
            <span className="text-on-surface font-semibold">+0.0003</span>
          </div>
          <div className="mt-2 w-full h-6">
            <svg className="w-full h-full text-secondary" preserveAspectRatio="none" viewBox="0 0 100 24">
              <path d="M 0 12 Q 25 8, 50 14 T 100 11" fill="none" stroke="currentColor" strokeWidth="1.8" />
            </svg>
          </div>
        </div>

        {/* Channel A-2 */}
        <div className="flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-secondary-container" />
              <span className="font-label-caps text-label-caps text-outline uppercase">Channel A-2</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-label-caps text-label-caps uppercase font-semibold">
              Nominal
            </span>
          </div>
          <div className="my-space-md">
            <span className="font-body-sm text-body-sm text-on-surface-variant block mb-1">Roll Axis Angular Rate</span>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                {a2 ? a2.currentValue.toFixed(4) : "0.0039"}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-outline">rad/s</span>
            </div>
          </div>
          <div className="pt-space-sm border-t border-surface-container flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <span className="text-on-surface-variant font-label-caps text-label-caps uppercase">Baseline Dev.</span>
            <span className="text-on-surface font-semibold">+0.0002</span>
          </div>
          <div className="mt-2 w-full h-6">
            <svg className="w-full h-full text-secondary-container" preserveAspectRatio="none" viewBox="0 0 100 24">
              <path d="M 0 14 L 20 11 L 40 15 L 60 12 L 80 14 L 100 12" fill="none" stroke="currentColor" strokeWidth="1.8" />
            </svg>
          </div>
        </div>

        {/* Channel A-3 */}
        <div className="flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-on-tertiary-container" />
              <span className="font-label-caps text-label-caps text-outline uppercase">Channel A-3</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-label-caps text-label-caps uppercase font-semibold">
              Nominal
            </span>
          </div>
          <div className="my-space-md">
            <span className="font-body-sm text-body-sm text-on-surface-variant block mb-1">Yaw Axis / RWA Momentum</span>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                {a3 ? a3.currentValue.toFixed(4) : "0.0011"}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-outline">rad/s</span>
            </div>
          </div>
          <div className="pt-space-sm border-t border-surface-container flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <span className="text-on-surface-variant font-label-caps text-label-caps uppercase">RWA #3 Spin</span>
            <span className="text-on-surface font-semibold">3,450 RPM</span>
          </div>
          <div className="mt-2 w-full h-6">
            <svg className="w-full h-full text-on-tertiary-container" preserveAspectRatio="none" viewBox="0 0 100 24">
              <path d="M 0 13 Q 30 16, 60 11 T 100 13" fill="none" stroke="currentColor" strokeWidth="1.8" />
            </svg>
          </div>
        </div>

        {/* Channel A-4 */}
        <div className="flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-primary-container" />
              <span className="font-label-caps text-label-caps text-outline uppercase">Channel A-4</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-label-caps text-label-caps uppercase font-semibold">
              Nominal
            </span>
          </div>
          <div className="my-space-md">
            <span className="font-body-sm text-body-sm text-on-surface-variant block mb-1">Star Tracker Slew Rate</span>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                {a4 ? a4.currentValue.toFixed(4) : "0.0015"}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-outline">rad/s</span>
            </div>
          </div>
          <div className="pt-space-sm border-t border-surface-container flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <span className="text-on-surface-variant font-label-caps text-label-caps uppercase">Tracker Conf.</span>
            <span className="text-on-tertiary-container font-semibold">99.8%</span>
          </div>
          <div className="mt-2 w-full h-6">
            <svg className="w-full h-full text-outline" preserveAspectRatio="none" viewBox="0 0 100 24">
              <path d="M 0 12 L 25 13 L 50 11 L 75 12 L 100 11" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </div>
        </div>
      </div>

      {/* Anomaly Event Timeline & Health Status Breakdown (Exact from Stitch) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-lg">
        {/* Event Timeline & Pass Log (Col 7) */}
        <div className="xl:col-span-7 flex flex-col p-space-md rounded bg-surface-container-lowest shadow-sm">
          <div className="flex items-center justify-between pb-space-sm mb-space-sm">
            <div className="flex items-center gap-space-sm">
              <span className="font-headline-sm text-headline-sm text-on-surface">Maneuver &amp; Orbital Pass Timeline</span>
              <span className="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-label-caps text-label-caps uppercase font-semibold">
                0 Anomaly Events / 24 Passes
              </span>
            </div>
            <span className="font-label-caps text-label-caps text-outline uppercase hidden sm:inline">Verification: EKF-SVM</span>
          </div>
          <div className="flex flex-col gap-space-sm">
            {/* Event 1 */}
            <div className="flex items-start gap-space-md p-space-sm rounded bg-surface-container-low">
              <div className="w-2 h-2 mt-1.5 rounded-full bg-on-tertiary-container shrink-0" />
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-headline-sm text-[13px] font-semibold text-on-surface">Target Alignment Slew: Earth Observing Node 3</span>
                  <span className="font-mono-data-sm text-[11px] text-on-surface-variant">MET +142:07:44:10</span>
                </div>
                <p className="font-body-sm text-[12px] text-on-surface-variant truncate">
                  Angular displacement of 1.42° completed within 42.1 seconds. Pointing steady state achieved with &lt; 0.008° jitter.
                </p>
              </div>
              <div className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-surface-container-lowest text-on-tertiary-container shrink-0 font-medium">
                SUCCESS
              </div>
            </div>

            {/* Event 2 */}
            <div className="flex items-start gap-space-md p-space-sm rounded bg-surface-container-low">
              <div className="w-2 h-2 mt-1.5 rounded-full bg-secondary shrink-0" />
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-headline-sm text-[13px] font-semibold text-on-surface">Magnetic Torquer Momentum Dump Cycle</span>
                  <span className="font-mono-data-sm text-[11px] text-on-surface-variant">MET +142:06:12:00</span>
                </div>
                <p className="font-body-sm text-[12px] text-on-surface-variant truncate">
                  MTQ coils #1 and #3 energized against Geomagnetic Field. RWA #1-4 spin rates stabilized to nominal 3,200 - 3,500 RPM envelope.
                </p>
              </div>
              <div className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-surface-container-lowest text-on-surface shrink-0 font-medium">
                VERIFIED
              </div>
            </div>

            {/* Event 3 */}
            <div className="flex items-start gap-space-md p-space-sm rounded bg-surface-container-low">
              <div className="w-2 h-2 mt-1.5 rounded-full bg-on-tertiary-container shrink-0" />
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-headline-sm text-[13px] font-semibold text-on-surface">Orbital Pass #24 Meridian Transit</span>
                  <span className="font-mono-data-sm text-[11px] text-on-surface-variant">MET +142:04:30:22</span>
                </div>
                <p className="font-body-sm text-[12px] text-on-surface-variant truncate">
                  Ground station Svalbard uplink confirmed 0 dropped telemetry packages. Gyro bias estimation converged at 0.0001°/hr.
                </p>
              </div>
              <div className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-surface-container-lowest text-on-tertiary-container shrink-0 font-medium">
                AUDITED
              </div>
            </div>

            {/* Event 4 */}
            <div className="flex items-start gap-space-md p-space-sm rounded bg-surface-container-low">
              <div className="w-2 h-2 mt-1.5 rounded-full bg-outline shrink-0" />
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-headline-sm text-[13px] font-semibold text-on-surface">Sun Sensor Solar Eclipse Ingress &amp; Handover</span>
                  <span className="font-mono-data-sm text-[11px] text-on-surface-variant">MET +142:02:55:04</span>
                </div>
                <p className="font-body-sm text-[12px] text-on-surface-variant truncate">
                  Automated switch to dual Star Tracker guidance with zero attitude drift during umbra transition.
                </p>
              </div>
              <div className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-surface-container-lowest text-on-surface shrink-0 font-medium">
                ROUTINE
              </div>
            </div>
          </div>
        </div>

        {/* Attitude Subsystem Health Status breakdown (Col 5) */}
        <div className="xl:col-span-5 flex flex-col justify-between p-space-md rounded bg-surface-container-lowest shadow-sm">
          <div>
            <div className="flex items-center justify-between pb-space-sm mb-space-sm">
              <span className="font-headline-sm text-headline-sm text-on-surface">Hardware Health Integrity</span>
              <span className="font-label-caps text-label-caps px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-semibold uppercase">
                100% Operational
              </span>
            </div>
            <div className="flex flex-col gap-space-md">
              {/* Reaction Wheels */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-body-sm text-body-sm font-semibold text-on-surface">Reaction Wheels (RWA 1-4)</span>
                    <span className="font-label-caps text-label-caps px-1.5 py-0.2 rounded bg-surface-container text-on-surface uppercase">
                      4 of 4 ACTIVE
                    </span>
                  </div>
                  <span className="text-on-tertiary-container font-bold">100%</span>
                </div>
                <div className="w-full h-2 rounded bg-surface-container-low overflow-hidden">
                  <div className="h-full bg-on-tertiary-container rounded" style={{ width: "100%" }} />
                </div>
                <div className="flex items-center justify-between font-mono-data-sm text-[11px] text-on-surface-variant">
                  <span>Bearing Temp: +18.4°C</span>
                  <span>Avg Current: 0.42A</span>
                  <span>Vibration: &lt; 0.01g</span>
                </div>
              </div>

              {/* Magnetorquers */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-body-sm text-body-sm font-semibold text-on-surface">Magnetorquers (MTQ X/Y/Z)</span>
                    <span className="font-label-caps text-label-caps px-1.5 py-0.2 rounded bg-surface-container text-on-surface uppercase">
                      TRIAXIAL SYNC
                    </span>
                  </div>
                  <span className="text-on-tertiary-container font-bold">100%</span>
                </div>
                <div className="w-full h-2 rounded bg-surface-container-low overflow-hidden">
                  <div className="h-full bg-on-tertiary-container rounded" style={{ width: "100%" }} />
                </div>
                <div className="flex items-center justify-between font-mono-data-sm text-[11px] text-on-surface-variant">
                  <span>Magnetic Moment: 12.0 Am²</span>
                  <span>Coil Resistance: 48.2 Ω</span>
                  <span>Duty Cycle: 14%</span>
                </div>
              </div>

              {/* Sun Sensors */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-body-sm text-body-sm font-semibold text-on-surface">Fine Sun Sensors (FSS A/B)</span>
                    <span className="font-label-caps text-label-caps px-1.5 py-0.2 rounded bg-surface-container text-on-surface uppercase">
                      DUAL REDUNDANT
                    </span>
                  </div>
                  <span className="text-on-tertiary-container font-bold">100%</span>
                </div>
                <div className="w-full h-2 rounded bg-surface-container-low overflow-hidden">
                  <div className="h-full bg-on-tertiary-container rounded" style={{ width: "100%" }} />
                </div>
                <div className="flex items-center justify-between font-mono-data-sm text-[11px] text-on-surface-variant">
                  <span>FOV Accuracy: 0.01°</span>
                  <span>Cell Degradation: 0.0%</span>
                  <span>Solar Vector: Valid</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Action Calibration Control */}
          <div className="mt-space-md pt-space-sm border-t border-surface-container flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
              <span className="font-label-caps text-label-caps text-outline uppercase">
                Autonomous Gyro Drift Bias: 0.0001°/hr
              </span>
            </div>
            <button
              className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-label-caps uppercase transition-colors"
              type="button"
            >
              Run Diagnostics
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
