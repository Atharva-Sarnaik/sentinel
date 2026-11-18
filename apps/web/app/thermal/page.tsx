"use client";

import React, { useState } from "react";
import { useTelemetry } from "../../context/TelemetryContext";

export default function ThermalPage() {
  const { currentWindow } = useTelemetry();
  const thermal = currentWindow.subsystems.thermal;
  const [selectedChannel, setSelectedChannel] = useState<string>("all");
  const [timeWindow, setTimeWindow] = useState<string>("1h");

  const t1 = thermal.channels["T-1"];
  const t2 = thermal.channels["T-2"];
  const t3 = thermal.channels["T-3"];

  const isAnom = thermal.severity !== "nominal";
  const winNum = 1000 + currentWindow.windowIndex;

  // 16 window IDs for the heatmap (e.g. winNum - 15 .. winNum)
  const windowIds = Array.from({ length: 16 }, (_, i) => winNum - 15 + i);

  return (
    <div className="flex flex-col w-full gap-space-lg pb-12">
      {/* Subsystem Header Bar */}
      <section className="bg-surface-container-lowest rounded-lg p-space-lg shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-wrap items-center justify-between gap-space-md">
          <div className="flex items-center gap-space-md">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-secondary">
              <span className="material-symbols-outlined text-[24px]">thermostat</span>
            </div>
            <div>
              <div className="flex items-center gap-space-sm">
                <h1 className="font-headline-md text-headline-md text-on-surface">Thermal Subsystem (TCS)</h1>
                <span className={`px-2 py-0.5 rounded font-label-caps text-label-caps uppercase flex items-center gap-1 ${isAnom ? "bg-error-container text-on-error-container font-semibold" : "bg-surface-container text-on-tertiary-container"}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isAnom ? "bg-error" : "bg-on-tertiary-container"}`} />
                  {isAnom ? "THERMAL EXCURSION" : "NOMINAL"}
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-label-caps text-label-caps uppercase">
                  SEV: {isAnom ? "RED / LEVEL 2" : "GREEN / LEVEL 0"}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1 font-mono-data-sm text-mono-data-sm text-on-surface-variant">
                <span>Specialist Agent:</span>
                <span className="text-on-surface font-medium bg-surface-container-low px-1.5 py-0.5 rounded">{thermal.model}</span>
                <span className="text-outline">|</span>
                <span>Ref Orbit: LEO-540 Equinoctial</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-space-xl bg-surface-container-low px-space-md py-space-sm rounded-lg">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Anomaly Score</span>
              <div className="flex items-baseline gap-1">
                <span className={`font-mono-data-lg text-mono-data-lg font-semibold ${isAnom ? "text-error" : "text-on-surface"}`}>
                  {thermal.anomalyScore.toFixed(2)}
                </span>
                <span className="font-mono-data-sm text-mono-data-sm text-outline">/ 1.00</span>
              </div>
            </div>
            <div className="w-px h-8 bg-surface-container-high" />
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Config Threshold</span>
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-semibold">
                {thermal.threshold.toFixed(2)}
              </span>
            </div>
            <div className="w-px h-8 bg-surface-container-high" />
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Responsible Channels</span>
              <span className={`font-mono-data-sm text-mono-data-sm font-medium mt-1 ${isAnom ? "text-error font-bold" : "text-on-tertiary-container"}`}>
                {thermal.responsibleChannels.length > 0 ? thermal.responsibleChannels.join(", ") : "None (Equilibrium Maintained)"}
              </span>
            </div>
          </div>
        </div>

        {/* Filters & Secondary Meta */}
        <div className="flex flex-wrap items-center justify-between gap-space-md pt-space-xs">
          <div className="flex items-center gap-1.5" id="tcs-channel-filters">
            <button
              onClick={() => setSelectedChannel("all")}
              className={`filter-btn px-3 py-1.5 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "all" ? "bg-primary text-on-primary shadow-sm" : "bg-surface-container-low text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
              }`}
              type="button"
            >
              All Channels [3]
            </button>
            <button
              onClick={() => setSelectedChannel("t1")}
              className={`filter-btn px-3 py-1.5 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "t1" ? "bg-primary text-on-primary shadow-sm" : "bg-surface-container-low text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
              }`}
              type="button"
            >
              T-1 Payload Deck
            </button>
            <button
              onClick={() => setSelectedChannel("t2")}
              className={`filter-btn px-3 py-1.5 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "t2" ? "bg-primary text-on-primary shadow-sm" : "bg-surface-container-low text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
              }`}
              type="button"
            >
              T-2 Battery Enclosure
            </button>
            <button
              onClick={() => setSelectedChannel("t3")}
              className={`filter-btn px-3 py-1.5 rounded font-label-caps text-label-caps uppercase transition-colors ${
                selectedChannel === "t3" ? "bg-primary text-on-primary shadow-sm" : "bg-surface-container-low text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
              }`}
              type="button"
            >
              T-3 Radiator Panel
            </button>
          </div>

          <div className="flex items-center gap-space-md text-on-surface-variant font-mono-data-sm text-mono-data-sm">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-secondary rounded-full" />
              <span>T-1 Payload</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-inverse-surface rounded-full" />
              <span>T-2 Battery</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-secondary-container rounded-full" />
              <span>T-3 Radiator</span>
            </div>
          </div>
        </div>
      </section>

      {/* Individual Sensor Cards Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
        {/* Sensor T-1 */}
        <div className="bg-surface-container-lowest rounded-lg p-space-md shadow-sm relative overflow-hidden flex flex-col justify-between group hover:shadow-md transition-shadow">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-surface-container rounded-full opacity-40 pointer-events-none" />
          <div>
            <div className="flex items-center justify-between mb-space-xs">
              <span className="font-label-caps text-label-caps uppercase text-outline">CHANNEL T-01 // PRIMARY</span>
              <span className={`px-1.5 py-0.5 rounded font-label-caps text-label-caps uppercase flex items-center gap-1 ${isAnom ? "bg-error-container text-on-error-container" : "bg-surface-container text-on-tertiary-container"}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${isAnom ? "bg-error" : "bg-on-tertiary-container"}`} />
                {isAnom ? "ALERT" : "NOMINAL"}
              </span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Payload Instruments Deck</h3>
            <span className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">PT1000 Platinum RTD (Zone 1A)</span>
          </div>
          <div className="my-space-md flex items-baseline justify-between">
            <div>
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold">
                {t1 ? (t1.currentValue > 0 ? `+${t1.currentValue.toFixed(1)}` : t1.currentValue.toFixed(1)) : "+21.4"}
              </span>
              <span className="font-body-sm text-body-sm text-outline ml-0.5">°C</span>
            </div>
            <div className="text-right">
              <div className="font-label-caps text-label-caps text-outline uppercase">Hourly Drift</div>
              <span className="font-mono-data-md text-mono-data-md text-secondary font-medium">+0.02°C/hr</span>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between font-mono-data-sm text-[10px] text-outline mb-1">
              <span>Safe: -10°C</span>
              <span>Operating: +21.4°C</span>
              <span>Limit: +45°C</span>
            </div>
            <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden flex">
              <div className={`h-full rounded-full ${isAnom ? "bg-error" : "bg-secondary"}`} style={{ width: "58%" }} />
            </div>
            <div className="mt-space-sm flex items-center justify-between text-on-surface-variant font-mono-data-sm text-mono-data-sm">
              <span>Loop Feedback: Active PWM</span>
              <span className="text-on-surface">Duty 14.2%</span>
            </div>
          </div>
        </div>

        {/* Sensor T-2 */}
        <div className="bg-surface-container-lowest rounded-lg p-space-md shadow-sm relative overflow-hidden flex flex-col justify-between group hover:shadow-md transition-shadow">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-surface-container rounded-full opacity-40 pointer-events-none" />
          <div>
            <div className="flex items-center justify-between mb-space-xs">
              <span className="font-label-caps text-label-caps uppercase text-outline">CHANNEL T-02 // STORAGE</span>
              <span className="px-1.5 py-0.5 rounded bg-surface-container text-on-tertiary-container font-label-caps text-label-caps uppercase flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                NOMINAL
              </span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Battery Enclosure Core</h3>
            <span className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">Lithium-Iron-Phosphate Core Array</span>
          </div>
          <div className="my-space-md flex items-baseline justify-between">
            <div>
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold">
                {t2 ? (t2.currentValue > 0 ? `+${t2.currentValue.toFixed(1)}` : t2.currentValue.toFixed(1)) : "+18.2"}
              </span>
              <span className="font-body-sm text-body-sm text-outline ml-0.5">°C</span>
            </div>
            <div className="text-right">
              <div className="font-label-caps text-label-caps text-outline uppercase">Hourly Drift</div>
              <span className="font-mono-data-md text-mono-data-md text-on-tertiary-container font-medium">-0.01°C/hr</span>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between font-mono-data-sm text-[10px] text-outline mb-1">
              <span>Safe: 0°C</span>
              <span>Operating: +18.2°C</span>
              <span>Limit: +35°C</span>
            </div>
            <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden flex">
              <div className="h-full bg-inverse-surface rounded-full" style={{ width: "52%" }} />
            </div>
            <div className="mt-space-sm flex items-center justify-between text-on-surface-variant font-mono-data-sm text-mono-data-sm">
              <span>Heater Status: Quiescent</span>
              <span className="text-on-surface">Auto-Armed</span>
            </div>
          </div>
        </div>

        {/* Sensor T-3 */}
        <div className="bg-surface-container-lowest rounded-lg p-space-md shadow-sm relative overflow-hidden flex flex-col justify-between group hover:shadow-md transition-shadow">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-surface-container rounded-full opacity-40 pointer-events-none" />
          <div>
            <div className="flex items-center justify-between mb-space-xs">
              <span className="font-label-caps text-label-caps uppercase text-outline">CHANNEL T-03 // RADIATIVE</span>
              <span className="px-1.5 py-0.5 rounded bg-surface-container text-on-tertiary-container font-label-caps text-label-caps uppercase flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                NOMINAL
              </span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Deep Space Radiator Panel</h3>
            <span className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">Silver-Teflon OSR Outer Skin</span>
          </div>
          <div className="my-space-md flex items-baseline justify-between">
            <div>
              <span className="font-mono-data-lg text-mono-data-lg text-on-surface font-bold">
                {t3 ? t3.currentValue.toFixed(1) : "-4.6"}
              </span>
              <span className="font-body-sm text-body-sm text-outline ml-0.5">°C</span>
            </div>
            <div className="text-right">
              <div className="font-label-caps text-label-caps text-outline uppercase">Dissipation Rate</div>
              <span className="font-mono-data-md text-mono-data-md text-secondary-container font-semibold">142 W</span>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between font-mono-data-sm text-[10px] text-outline mb-1">
              <span>Min: -65°C</span>
              <span>Operating: -4.6°C</span>
              <span>Limit: +70°C</span>
            </div>
            <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden flex">
              <div className="h-full bg-secondary-container rounded-full" style={{ width: "44%" }} />
            </div>
            <div className="mt-space-sm flex items-center justify-between text-on-surface-variant font-mono-data-sm text-mono-data-sm">
              <span>Heat Pipe Flow: Steady</span>
              <span className="text-on-surface">Ammonia 98%</span>
            </div>
          </div>
        </div>
      </section>

      {/* Multi-Sensor Time-Series Telemetry Chart */}
      <section className="bg-surface-container-lowest rounded-lg p-space-lg shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-wrap items-center justify-between gap-space-md">
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold">Multi-Sensor Telemetry Time-Series</h2>
            <p className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">
              Continuous telemetry stream across orbital windows (Safe Corridor: -15.0°C to +45.0°C | Alert Threshold: +50.0°C)
            </p>
          </div>
          <div className="flex items-center gap-space-sm">
            <div className="flex items-center bg-surface-container-low rounded p-0.5 text-on-surface">
              {["30m", "1h", "3h", "12h"].map((windowKey) => (
                <button
                  key={windowKey}
                  onClick={() => setTimeWindow(windowKey)}
                  className={`px-2 py-1 rounded font-mono-data-sm text-mono-data-sm transition-colors ${
                    timeWindow === windowKey
                      ? "bg-surface-container-lowest text-on-surface font-medium shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                  type="button"
                >
                  {windowKey.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="h-4 w-px bg-surface-container" />
            <div className="flex items-center gap-1">
              <button className="p-1.5 rounded bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface flex items-center justify-center" title="Zoom in" type="button">
                <span className="material-symbols-outlined text-[18px]">zoom_in</span>
              </button>
              <button className="p-1.5 rounded bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface flex items-center justify-center" title="Zoom out" type="button">
                <span className="material-symbols-outlined text-[18px]">zoom_out</span>
              </button>
              <button className="p-1.5 rounded bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface flex items-center justify-center" title="Reset view" type="button">
                <span className="material-symbols-outlined text-[18px]">refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Chart Canvas Area */}
        <div className="relative w-full h-80 bg-surface-container-low rounded p-space-sm flex flex-col justify-between overflow-hidden">
          {/* Readout Tooltip Overlay */}
          <div className="absolute top-4 right-6 bg-surface-container-lowest/95 backdrop-blur px-space-md py-space-xs rounded shadow-md pointer-events-none flex items-center gap-space-lg text-on-surface z-10 border border-surface-container">
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-outline uppercase">Active Window</span>
              <span className="font-mono-data-sm text-mono-data-sm font-semibold">WIN #{winNum}:48s</span>
            </div>
            <div className="flex items-center gap-space-md font-mono-data-sm text-mono-data-sm">
              <div><span className="text-secondary font-medium">T-1:</span> {t1?.currentValue.toFixed(1)}°C</div>
              <div><span className="text-inverse-surface font-medium">T-2:</span> {t2?.currentValue.toFixed(1)}°C</div>
              <div><span className="text-secondary-container font-medium">T-3:</span> {t3?.currentValue.toFixed(1)}°C</div>
            </div>
          </div>

          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 280">
            <defs>
              <linearGradient id="safeCorridor" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#009668" stopOpacity="0.05" />
                <stop offset="100%" stopColor="#009668" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            <g stroke="#d3e4fe" strokeDasharray="3 3" strokeWidth="1">
              <line stroke="#ba1a1a" strokeDasharray="5 4" strokeWidth="1.5" x1="50" x2="980" y1="40" y2="40" />
              <line x1="50" x2="980" y1="58" y2="58" />
              <line x1="50" x2="980" y1="120" y2="120" />
              <line stroke="#c6c6cd" strokeDasharray="0" strokeWidth="1" x1="50" x2="980" y1="180" y2="180" />
              <line x1="50" x2="980" y1="220" y2="220" />
              <line x1="200" x2="200" y1="20" y2="250" />
              <line x1="380" x2="380" y1="20" y2="250" />
              <line x1="560" x2="560" y1="20" y2="250" />
              <line x1="740" x2="740" y1="20" y2="250" />
              <line x1="920" x2="920" y1="20" y2="250" />
            </g>

            {/* Safe Corridor Band (-15°C to +45°C) */}
            <rect fill="url(#safeCorridor)" height="162" width="930" x="50" y="58" />

            <text fill="#ba1a1a" fontFamily="JetBrains Mono" fontSize="10" fontWeight="600" x="56" y="36">
              CRITICAL ALERT THRESHOLD +50.0°C
            </text>
            <text fill="#009668" fontFamily="JetBrains Mono" fontSize="9" x="56" y="70">
              SAFE OPERATING BAND UPPER (+45.0°C)
            </text>
            <text fill="#009668" fontFamily="JetBrains Mono" fontSize="9" x="56" y="216">
              SAFE OPERATING BAND LOWER (-15.0°C)
            </text>

            {/* Y-Axis Labels */}
            <g fill="#76777d" fontFamily="JetBrains Mono" fontSize="10">
              <text x="10" y="44">+50°C</text>
              <text x="10" y="62">+45°C</text>
              <text x="10" y="124">+25°C</text>
              <text x="15" y="184">0°C</text>
              <text x="10" y="224">-15°C</text>
              <text x="10" y="260">-30°C</text>
            </g>

            {/* Series T-3: Radiator */}
            {(selectedChannel === "all" || selectedChannel === "t3") && (
              <path
                d="M 50,192 Q 130,195 210,198 T 370,190 T 530,196 T 690,191 T 850,194 L 980,193"
                fill="none"
                id="path-t3"
                stroke="#2170e4"
                strokeWidth={selectedChannel === "t3" ? "3" : "2"}
              />
            )}

            {/* Series T-2: Battery */}
            {(selectedChannel === "all" || selectedChannel === "t2") && (
              <path
                d="M 50,138 Q 140,136 230,137 T 390,139 T 550,136 T 710,138 T 870,137 L 980,137"
                fill="none"
                id="path-t2"
                stroke="#213145"
                strokeWidth={selectedChannel === "t2" ? "3" : "2"}
              />
            )}

            {/* Series T-1: Payload */}
            {(selectedChannel === "all" || selectedChannel === "t1") && (
              <path
                d={isAnom ? "M 50,128 Q 190,126 350,129 T 670,110 T 830,52 L 980,48" : "M 50,128 Q 120,130 190,126 T 350,129 T 510,124 T 670,128 T 830,126 L 980,127"}
                fill="none"
                id="path-t1"
                stroke={isAnom ? "#ba1a1a" : "#0058be"}
                strokeWidth={selectedChannel === "t1" || isAnom ? "3" : "2.5"}
              />
            )}

            {/* Interactive Vertical Hairline */}
            <g id="tracker-crosshair" transform="translate(850, 0)">
              <line stroke="#0058be" strokeDasharray="2 2" strokeWidth="1.5" x1="0" x2="0" y1="20" y2="250" />
              <circle cx="0" cy={isAnom ? 52 : 126} fill={isAnom ? "#ba1a1a" : "#0058be"} r="4" />
              <circle cx="0" cy="137" fill="#213145" r="4" />
              <circle cx="0" cy="194" fill="#2170e4" r="4" />
            </g>

            {/* X-Axis Labels */}
            <g fill="#76777d" fontFamily="JetBrains Mono" fontSize="10">
              <text x="50" y="270">13:50 UTC</text>
              <text x="200" y="270">14:00 UTC</text>
              <text x="380" y="270">14:10 UTC</text>
              <text x="560" y="270">14:20 UTC</text>
              <text x="740" y="270">14:30 UTC</text>
              <text x="920" y="270">14:40 UTC</text>
            </g>
          </svg>
        </div>

        {/* Chart Footer Operational Notes */}
        <div className="flex flex-wrap items-center justify-between text-on-surface-variant font-mono-data-sm text-mono-data-sm pt-space-xs">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-[16px] text-on-tertiary-container">verified</span>
            <span>Sensor Telemetry Confidence: <strong className="text-on-surface font-semibold">99.8%</strong> (Zero dropouts detected)</span>
          </div>
          <div className="flex items-center gap-space-md">
            <span>Eclipse Ingress: <strong className="text-on-surface font-medium">MET +142:09:12:00</strong></span>
            <span className="text-outline">|</span>
            <span>Predicted Solar Flux: <strong className="text-on-surface font-medium">1361.2 W/m²</strong></span>
          </div>
        </div>
      </section>

      {/* Thermal Anomaly Score & Deviation Heatmap Matrix (Exact from Stitch) */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-space-md">
        {/* Heatmap Matrix (2 cols on lg) */}
        <div className="lg:col-span-2 bg-surface-container-lowest rounded-lg p-space-lg shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-space-sm">
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">Discrete Window Deviation Heatmap</h3>
                <p className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">
                  Sensor delta from nominal equilibrium model across historical telemetry windows
                </p>
              </div>
              <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-mono-data-sm text-mono-data-sm">
                RES: 30s/BIN
              </span>
            </div>

            {/* Heatmap Grid */}
            <div className="mt-space-md flex flex-col gap-2">
              {/* T-1 Row */}
              <div className="flex items-center gap-2">
                <span className="w-16 font-mono-data-sm text-mono-data-sm text-on-surface font-medium">T-1 PLD</span>
                <div className="grid grid-cols-16 gap-1 flex-1 h-6">
                  {windowIds.map((w, idx) => {
                    const isLast = idx === 15;
                    const bgClass = isLast && isAnom ? "bg-error" : idx % 5 === 0 ? "bg-surface-container-high" : "bg-surface-container";
                    return (
                      <div
                        key={w}
                        className={`${bgClass} rounded-sm`}
                        title={`Win ${w}: ${isLast && isAnom ? "0.38 dev (ANOMALY)" : "0.02 dev"}`}
                      />
                    );
                  })}
                </div>
              </div>

              {/* T-2 Row */}
              <div className="flex items-center gap-2">
                <span className="w-16 font-mono-data-sm text-mono-data-sm text-on-surface font-medium">T-2 BAT</span>
                <div className="grid grid-cols-16 gap-1 flex-1 h-6">
                  {windowIds.map((w, idx) => (
                    <div
                      key={w}
                      className={`${idx === 7 ? "bg-surface-container-high" : "bg-surface-container"} rounded-sm`}
                    />
                  ))}
                </div>
              </div>

              {/* T-3 Row */}
              <div className="flex items-center gap-2">
                <span className="w-16 font-mono-data-sm text-mono-data-sm text-on-surface font-medium">T-3 RAD</span>
                <div className="grid grid-cols-16 gap-1 flex-1 h-6">
                  {windowIds.map((w, idx) => (
                    <div
                      key={w}
                      className={`${idx === 1 || idx === 2 || idx === 13 ? "bg-surface-container-high" : "bg-surface-container"} rounded-sm`}
                    />
                  ))}
                </div>
              </div>

              {/* Window Indexes */}
              <div className="flex items-center gap-2 pt-1">
                <span className="w-16 font-label-caps text-label-caps text-outline uppercase">WIN ID</span>
                <div className="grid grid-cols-16 gap-1 flex-1 font-mono-data-sm text-[9px] text-outline text-center">
                  {windowIds.map((w, idx) => (
                    <span key={w} className={idx === 15 ? "text-on-surface font-semibold" : ""}>
                      {w}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Heatmap Legend */}
          <div className="mt-space-md pt-space-sm flex items-center justify-between font-mono-data-sm text-mono-data-sm text-on-surface-variant">
            <div className="flex items-center gap-space-sm">
              <span>Deviation Scale:</span>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-sm bg-surface-container" />
                <span className="font-mono-data-sm text-[10px]">&lt;0.05 (Min)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-sm bg-surface-container-high" />
                <span className="font-mono-data-sm text-[10px]">0.05-0.15</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-sm bg-surface-container-highest" />
                <span className="font-mono-data-sm text-[10px]">&gt;0.15</span>
              </div>
            </div>
            <div className="font-label-caps text-label-caps text-outline uppercase">
              Zero Out-Of-Family Traces
            </div>
          </div>
        </div>

        {/* AI Model Confidence & Diagnostics (1 col on lg) */}
        <div className="bg-surface-container-lowest rounded-lg p-space-lg shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-space-sm">
              <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">Predictor Diagnostics</h3>
              <span className="px-1.5 py-0.5 rounded bg-surface-container text-on-tertiary-container font-label-caps text-label-caps uppercase">
                LIVE AGENT
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Thermal LSTM recurrent network evaluating latent gradient transitions across orbital night/day shifts.
            </p>

            {/* Confidence Gauge Bar */}
            <div className="mt-space-md p-space-sm rounded bg-surface-container-low flex flex-col gap-1.5">
              <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase">
                <span>Model Confidence</span>
                <span className="font-mono-data-sm text-mono-data-sm text-on-surface font-bold">99.1%</span>
              </div>
              <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-secondary rounded-full" style={{ width: "99.1%" }} />
              </div>
              <div className="flex justify-between font-mono-data-sm text-[10px] text-outline">
                <span>Loss: 0.0014</span>
                <span>State: Convergence</span>
              </div>
            </div>

            {/* Telemetry Parameters List */}
            <div className="mt-space-md flex flex-col gap-2 font-mono-data-sm text-mono-data-sm">
              <div className="flex items-center justify-between py-1 bg-surface-container-low px-2 rounded">
                <span className="text-outline">Max Observed Flux:</span>
                <span className="font-semibold text-on-surface">144.1 W</span>
              </div>
              <div className="flex items-center justify-between py-1 bg-surface-container-low px-2 rounded">
                <span className="text-outline">Thermostat Relay K1:</span>
                <span className="font-semibold text-on-tertiary-container">OPEN (NOMINAL)</span>
              </div>
              <div className="flex items-center justify-between py-1 bg-surface-container-low px-2 rounded">
                <span className="text-outline">Heater Line #2 Draw:</span>
                <span className="font-semibold text-on-surface">0.00 A (IDLE)</span>
              </div>
              <div className="flex items-center justify-between py-1 bg-surface-container-low px-2 rounded">
                <span className="text-outline">Reconstructed Drift:</span>
                <span className="font-semibold text-on-surface">&lt; 0.015°C/hr</span>
              </div>
            </div>
          </div>

          {/* Action Verification Button */}
          <div className="mt-space-md pt-space-sm flex items-center justify-between">
            <button
              className="w-full flex items-center justify-center gap-2 py-2 px-space-md rounded bg-primary text-on-primary hover:bg-inverse-surface font-label-caps text-label-caps uppercase transition-colors shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">tune</span>
              <span>Calibrate Heat Balance Threshold</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
