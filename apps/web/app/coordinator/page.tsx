'use client';

import React, { useState } from 'react';
import { useTelemetry } from '@/context/TelemetryContext';
import { ReplayPanel } from '@/components/replay/ReplayPanel';

export default function CoordinatorFusionPage() {
  const { currentWindow, exportAuditReport, latestBackendResponse } = useTelemetry();
  const [copiedHash, setCopiedHash] = useState(false);

  const isNominal = currentWindow.status === 'NORMAL';
  const severityBadgeBg = isNominal ? 'bg-surface-container-low text-on-tertiary-container' : 'bg-error-container text-on-error-container';
  const severityDotBg = isNominal ? 'bg-on-tertiary-container' : 'bg-error';

  const pwrScore = currentWindow.subsystems.power.anomalyScore;
  const pwrThresh = currentWindow.subsystems.power.threshold;
  const thmScore = currentWindow.subsystems.thermal.anomalyScore;
  const thmThresh = currentWindow.subsystems.thermal.threshold;
  const attScore = currentWindow.subsystems.attitude.anomalyScore;
  const attThresh = currentWindow.subsystems.attitude.threshold;
  const comScore = currentWindow.subsystems.communications.anomalyScore;
  const comThresh = currentWindow.subsystems.communications.threshold;

  // Radar coordinates centered at (100, 100), max radius 80
  const rPwr = Math.min(80, Math.max(12, pwrScore * 80));
  const rAdcs = Math.min(80, Math.max(12, attScore * 80));
  const rThm = Math.min(80, Math.max(12, thmScore * 80));
  const rCom = Math.min(80, Math.max(12, comScore * 80));

  const pwrY = 100 - rPwr;
  const adcsX = 100 + rAdcs;
  const thmY = 100 + rThm;
  const comX = 100 - rCom;
  const radarPolygon = `100,${pwrY} ${adcsX},100 100,${thmY} ${comX},100`;

  const radialMarginPct = Math.max(5, Math.round((1 - Math.max(pwrScore, thmScore, attScore, comScore)) * 100));

  const handleCopyHash = () => {
    navigator.clipboard.writeText(currentWindow.auditLog.hash).then(() => {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }).catch(() => {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    });
  };

  const winNum = 1000 + currentWindow.windowIndex;

  return (
    <div className="flex flex-col w-full gap-space-lg pb-12">
      {/* Operational Breadcrumb & Live Synapse Marker */}
      <div className="flex flex-wrap items-center justify-between gap-y-2">
        <div className="flex items-center gap-space-sm font-label-caps text-label-caps">
          <span className="text-on-surface-variant uppercase tracking-widest">MISSION DIRECTORY</span>
          <span className="text-outline-variant">/</span>
          <span className="text-on-surface-variant uppercase tracking-widest">AUTONOMOUS SUBSYSTEMS</span>
          <span className="text-outline-variant">/</span>
          <span className="text-secondary font-semibold uppercase tracking-widest">COORDINATOR &amp; FUSION CENTER</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-surface-container-low text-on-surface">
          <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container animate-pulse"></span>
          <span className="font-mono-data-sm text-mono-data-sm text-on-surface">FUSION_ENGINE_BUILD::v4.19-STABLE</span>
          <span className="font-label-caps text-label-caps px-1 py-0.5 rounded bg-surface-container text-on-surface-variant font-mono">LATENCY: 14ms</span>
        </div>
      </div>

      {/* NASA Historical Telemetry Replay Control Console (Phase 3) */}
      <ReplayPanel />

      {/* SECTION 1: Mission Decision Summary (Top Highlight Hero Bento) */}
      <section className="relative w-full overflow-hidden rounded-lg bg-surface-container-lowest p-space-lg shadow-sm">
        {/* Subtle gradient background accent */}
        <div className="absolute -right-24 -top-24 w-96 h-96 rounded-full bg-gradient-to-br from-tertiary-fixed-dim/20 to-secondary-fixed/30 blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col xl:flex-row gap-space-lg justify-between">
          {/* Left side: Status & Core Classification */}
          <div className="flex-1 flex flex-col gap-space-md">
            <div className="flex flex-wrap items-center gap-space-sm">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded font-label-caps text-label-caps font-semibold ${severityBadgeBg}`}>
                <span className={`w-2 h-2 rounded-full ${severityDotBg}`}></span>
                {isNominal ? 'NOMINAL (LEVEL 0 - GREEN)' : `ANOMALY DETECTED (${currentWindow.fusionDecision.severity.toUpperCase()})`}
              </span>
              <span className="font-mono-data-sm text-mono-data-sm text-on-surface-variant">
                CORROBORATION ID: <span className="font-semibold text-on-surface">#{currentWindow.fusionDecision.corroborationRule}</span>
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-label-caps text-label-caps">
                FRAME CONCURRENCE: {currentWindow.fusionDecision.concurrenceRatio} AGENTS
              </span>
            </div>

            <div>
              <div className="font-label-caps text-label-caps text-outline uppercase tracking-wider mb-1">
                Attributed Root Cause Diagnosis
              </div>
              <h1 className="font-headline-md text-headline-md font-bold text-on-surface tracking-tight uppercase">
                {isNominal ? 'NO ANOMALY DETECTED // SYSTEM IN STEADY ORBITAL EQUILIBRIUM' : currentWindow.fusionDecision.attributedSubsystem}
              </h1>
              <p className="mt-1 font-body-md text-body-md text-on-surface-variant max-w-4xl">
                {isNominal
                  ? 'Multi-Subsystem Threshold Concurrence confirmed zero divergent telemetry signatures across bus voltage, deck thermodynamics, momentum vector rates, and S/X RF link margins.'
                  : currentWindow.fusionDecision.explanationText}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-md pt-space-xs">
              <div className="p-space-sm rounded bg-surface-container-low">
                <span className="font-label-caps text-label-caps text-outline uppercase">Calibrated Anomaly Prob</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                    {currentWindow.bayesianAnomalyProb.toFixed(3)}
                  </span>
                  <span className={`font-label-caps text-label-caps font-medium ${isNominal ? 'text-on-tertiary-container' : 'text-error'}`}>
                    {isNominal ? '-0.004' : '+0.812'}
                  </span>
                </div>
                <span className="font-mono-data-sm text-[10px] text-on-surface-variant">Bayesian Laplace Prior</span>
              </div>

              <div className="p-space-sm rounded bg-surface-container-low">
                <span className="font-label-caps text-label-caps text-outline uppercase">Active Ensemble</span>
                <div className="mt-1 font-mono-data-lg text-mono-data-lg font-bold text-on-surface">4 Nodes</div>
                <span className="font-mono-data-sm text-[10px] text-on-surface-variant">Weights: Synchronized</span>
              </div>

              <div className="p-space-sm rounded bg-surface-container-low">
                <span className="font-label-caps text-label-caps text-outline uppercase">Consensus Entropy</span>
                <div className="mt-1 font-mono-data-lg text-mono-data-lg font-bold text-on-surface">
                  {currentWindow.fusionDecision.consensusEntropy.toFixed(3)} <span className="text-body-sm font-normal text-outline">nats</span>
                </div>
                <span className={`font-mono-data-sm text-[10px] ${isNominal ? 'text-on-tertiary-container' : 'text-error'}`}>
                  {isNominal ? 'Ultra-Low Dispersion' : 'High Dispersion Flagged'}
                </span>
              </div>

              <div className="p-space-sm rounded bg-surface-container-low">
                <span className="font-label-caps text-label-caps text-outline uppercase">Decision Hash</span>
                <div className="mt-1 font-mono-data-lg text-mono-data-lg font-bold text-on-surface truncate">
                  {currentWindow.auditLog.hash.slice(0, 7)}...{currentWindow.auditLog.hash.slice(-5)}
                </div>
                <span className="font-mono-data-sm text-[10px] text-on-surface-variant">SHA-256 Validated</span>
              </div>
            </div>
          </div>

          {/* Right side: Quick Action Controls & Cryptographic Badge */}
          <div className="xl:w-80 flex flex-col justify-between p-space-md rounded bg-surface-container-low gap-space-md">
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps uppercase text-outline">Decision Artifact</span>
                <span className="inline-flex items-center gap-1 font-mono-data-sm text-[11px] text-on-surface font-semibold">
                  <span className="material-symbols-outlined text-[14px] text-secondary">verified</span>
                  SIGNED &amp; SEALED
                </span>
              </div>
              <div className="font-mono-data-sm text-mono-data-sm text-on-surface-variant break-all bg-surface-container-lowest p-2 rounded">
                urn:sentinel:rec:{currentWindow.timestamp.replace(/[- :]/g, '').slice(0, 8)}-{winNum}:fusion:{currentWindow.auditLog.decisionId}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <button
                onClick={handleCopyHash}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded bg-surface-container-lowest hover:bg-surface-container text-on-surface font-mono-data-sm text-mono-data-sm transition-all shadow-sm"
                type="button"
              >
                <span className={`material-symbols-outlined text-[16px] ${copiedHash ? 'text-on-tertiary-container' : ''}`}>
                  {copiedHash ? 'done' : 'content_copy'}
                </span>
                <span>{copiedHash ? 'Hash Copied!' : 'Copy Decision Hash'}</span>
              </button>

              <button
                onClick={exportAuditReport}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded bg-primary text-on-primary font-mono-data-sm text-mono-data-sm font-medium hover:bg-inverse-surface transition-all shadow-sm"
                type="button"
              >
                <span className="material-symbols-outlined text-[16px]">terminal</span>
                <span>Download Audited JSON</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: Specialist Anomaly vs Threshold Bar Chart & Spatial Radar */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg">
        {/* Specialist Comparison Bar Chart (Col 8) */}
        <div className="lg:col-span-8 rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex flex-wrap items-center justify-between pb-space-sm gap-2">
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Multi-Agent Sensor Variance</span>
                <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">Specialist Agent Anomaly Scores vs. Active Alarm Limits</h2>
              </div>
              <div className="flex items-center gap-3 font-mono-data-sm text-mono-data-sm">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-secondary"></span>
                  <span className="text-on-surface-variant">Calculated Score</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-outline-variant"></span>
                  <span className="text-on-surface-variant">Threshold Limit</span>
                </div>
              </div>
            </div>

            {/* High-contrast Aerospace Chart Grid */}
            <div className="mt-space-md flex flex-col gap-space-md">
              {/* Power Specialist */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px] text-on-surface">bolt</span>
                    <span className="font-semibold text-on-surface">Power Subsystem Agent</span>
                    <span className="text-on-surface-variant font-mono-data-sm">(EPS-BUS-A/B)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-on-surface">Score: <strong className="font-mono-data-md">{pwrScore.toFixed(2)}</strong></span>
                    <span className="text-outline">/ Max Limit: {pwrThresh.toFixed(2)}</span>
                    <span className={`px-1.5 py-0.2 rounded font-label-caps text-[10px] font-bold ${pwrScore > pwrThresh ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-on-tertiary-container'}`}>
                      {pwrScore > pwrThresh ? 'ANOMALOUS' : 'NOMINAL'}
                    </span>
                  </div>
                </div>
                <div className="relative w-full h-7 bg-surface-container-low rounded overflow-hidden flex items-center px-1">
                  <div className="absolute top-0 bottom-0 w-0.5 bg-outline z-20" style={{ left: `${pwrThresh * 100}%` }}></div>
                  <span className="absolute top-1 font-mono-data-sm text-[9px] text-outline z-20 pointer-events-none" style={{ left: `calc(${pwrThresh * 100}% + 4px)` }}>
                    THRESH {pwrThresh.toFixed(2)}
                  </span>
                  <div
                    className={`h-5 rounded-sm transition-all duration-700 relative z-10 flex items-center justify-end pr-2 ${pwrScore > pwrThresh ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${Math.max(4, Math.min(100, pwrScore * 100))}%` }}
                  >
                    <span className="font-mono-data-sm text-[10px] text-on-secondary font-bold">{pwrScore.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Thermal Specialist */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px] text-on-surface">device_thermostat</span>
                    <span className="font-semibold text-on-surface">Thermal Subsystem Agent</span>
                    <span className="text-on-surface-variant font-mono-data-sm">(RAD-DECK-TEMP)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-on-surface">Score: <strong className="font-mono-data-md">{thmScore.toFixed(2)}</strong></span>
                    <span className="text-outline">/ Max Limit: {thmThresh.toFixed(2)}</span>
                    <span className={`px-1.5 py-0.2 rounded font-label-caps text-[10px] font-bold ${thmScore > thmThresh ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-on-tertiary-container'}`}>
                      {thmScore > thmThresh ? 'ANOMALOUS' : 'NOMINAL'}
                    </span>
                  </div>
                </div>
                <div className="relative w-full h-7 bg-surface-container-low rounded overflow-hidden flex items-center px-1">
                  <div className="absolute top-0 bottom-0 w-0.5 bg-outline z-20" style={{ left: `${thmThresh * 100}%` }}></div>
                  <span className="absolute top-1 font-mono-data-sm text-[9px] text-outline z-20 pointer-events-none" style={{ left: `calc(${thmThresh * 100}% + 4px)` }}>
                    THRESH {thmThresh.toFixed(2)}
                  </span>
                  <div
                    className={`h-5 rounded-sm transition-all duration-700 relative z-10 flex items-center justify-end pr-2 ${thmScore > thmThresh ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${Math.max(4, Math.min(100, thmScore * 100))}%` }}
                  >
                    <span className="font-mono-data-sm text-[10px] text-on-secondary font-bold">{thmScore.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Attitude Specialist */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px] text-on-surface">explore</span>
                    <span className="font-semibold text-on-surface">Attitude &amp; ADCS Agent</span>
                    <span className="text-on-surface-variant font-mono-data-sm">(GYRO-RWA-SYNC)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-on-surface">Score: <strong className="font-mono-data-md">{attScore.toFixed(2)}</strong></span>
                    <span className="text-outline">/ Max Limit: {attThresh.toFixed(2)}</span>
                    <span className={`px-1.5 py-0.2 rounded font-label-caps text-[10px] font-bold ${attScore > attThresh ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-on-tertiary-container'}`}>
                      {attScore > attThresh ? 'ANOMALOUS' : 'NOMINAL'}
                    </span>
                  </div>
                </div>
                <div className="relative w-full h-7 bg-surface-container-low rounded overflow-hidden flex items-center px-1">
                  <div className="absolute top-0 bottom-0 w-0.5 bg-outline z-20" style={{ left: `${attThresh * 100}%` }}></div>
                  <span className="absolute top-1 font-mono-data-sm text-[9px] text-outline z-20 pointer-events-none" style={{ left: `calc(${attThresh * 100}% + 4px)` }}>
                    THRESH {attThresh.toFixed(2)}
                  </span>
                  <div
                    className={`h-5 rounded-sm transition-all duration-700 relative z-10 flex items-center justify-end pr-2 ${attScore > attThresh ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${Math.max(4, Math.min(100, attScore * 100))}%` }}
                  >
                    <span className="font-mono-data-sm text-[10px] text-on-secondary font-bold">{attScore.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Communications Specialist */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-mono-data-sm text-mono-data-sm">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px] text-on-surface">settings_input_antenna</span>
                    <span className="font-semibold text-on-surface">Communications Agent</span>
                    <span className="text-on-surface-variant font-mono-data-sm">(RF-S/X-LOCK)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-on-surface">Score: <strong className="font-mono-data-md">{comScore.toFixed(2)}</strong></span>
                    <span className="text-outline">/ Max Limit: {comThresh.toFixed(2)}</span>
                    <span className={`px-1.5 py-0.2 rounded font-label-caps text-[10px] font-bold ${comScore > comThresh ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-on-tertiary-container'}`}>
                      {comScore > comThresh ? 'ANOMALOUS' : 'NOMINAL'}
                    </span>
                  </div>
                </div>
                <div className="relative w-full h-7 bg-surface-container-low rounded overflow-hidden flex items-center px-1">
                  <div className="absolute top-0 bottom-0 w-0.5 bg-outline z-20" style={{ left: `${comThresh * 100}%` }}></div>
                  <span className="absolute top-1 font-mono-data-sm text-[9px] text-outline z-20 pointer-events-none" style={{ left: `calc(${comThresh * 100}% + 4px)` }}>
                    THRESH {comThresh.toFixed(2)}
                  </span>
                  <div
                    className={`h-5 rounded-sm transition-all duration-700 relative z-10 flex items-center justify-end pr-2 ${comScore > comThresh ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${Math.max(4, Math.min(100, comScore * 100))}%` }}
                  >
                    <span className="font-mono-data-sm text-[10px] text-on-secondary font-bold">{comScore.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Micro Sparkline Scale Baseline Footer */}
          <div className="mt-space-md pt-space-sm flex items-center justify-between font-mono-data-sm text-[11px] text-outline">
            <span>0.00 (Zero Drift)</span>
            <span>0.25</span>
            <span>0.50 (Pre-Alarm Warning)</span>
            <span>0.75 (Critical Intercept)</span>
            <span>1.00 (Anomaly Confirmed)</span>
          </div>
        </div>

        {/* Live Telemetry State Radar / Orthogonal Visual (Col 4) */}
        <div className="lg:col-span-4 rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col justify-between">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-label-caps text-outline uppercase">Spatial Corroboration</span>
              <span className="font-mono-data-sm text-mono-data-sm px-1.5 py-0.5 rounded bg-surface-container text-on-tertiary-container font-semibold">
                QUAD SYNC
              </span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Agent Confidence Radial</h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Concentric geometric projection of specialist variance profiles within safe orbital bounds.
            </p>
          </div>

          {/* Vector Radar Graphic */}
          <div className="relative my-4 flex items-center justify-center">
            <svg className="w-48 h-48 text-surface-container" fill="none" viewBox="0 0 200 200">
              {/* Concentric bounds */}
              <circle cx="100" cy="100" r="80" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" />
              <circle cx="100" cy="100" r="55" stroke="currentColor" strokeWidth="1" />
              <circle cx="100" cy="100" r="30" stroke="currentColor" strokeWidth="1" />

              {/* Orthogonal Axes */}
              <line stroke="currentColor" strokeWidth="1" x1="100" x2="100" y1="10" y2="190" />
              <line stroke="currentColor" strokeWidth="1" x1="10" x2="190" y1="100" y2="100" />

              {/* Active Confidence Polygon */}
              <polygon
                className={isNominal ? 'fill-secondary/15 stroke-secondary' : 'fill-error/20 stroke-error'}
                points={radarPolygon}
                strokeWidth="2"
              />

              {/* Node Dots */}
              <circle className={isNominal ? 'fill-secondary' : 'fill-error'} cx="100" cy={pwrY} r="3" />
              <circle className={isNominal ? 'fill-secondary' : 'fill-error'} cx={adcsX} cy="100" r="3" />
              <circle className={isNominal ? 'fill-secondary' : 'fill-error'} cx={thmY} cy="100" r="3" />
              <circle className={isNominal ? 'fill-secondary' : 'fill-error'} cx={comX} cy="100" r="3" />

              {/* Agent labels */}
              <text className="fill-outline text-[9px] font-mono" textAnchor="middle" x="100" y="8">PWR</text>
              <text className="fill-outline text-[9px] font-mono" textAnchor="end" x="194" y="103">ADCS</text>
              <text className="fill-outline text-[9px] font-mono" textAnchor="middle" x="100" y="198">THM</text>
              <text className="fill-outline text-[9px] font-mono" textAnchor="start" x="6" y="103">COMM</text>
            </svg>
          </div>

          <div className="p-space-sm rounded bg-surface-container-low flex items-center justify-between font-mono-data-sm text-mono-data-sm">
            <span className="text-on-surface-variant">Radial Margin:</span>
            <span className={`font-bold ${isNominal ? 'text-on-surface' : 'text-error'}`}>
              +{radialMarginPct}% Clearance
            </span>
          </div>
        </div>
      </section>

      {/* SECTION 3: Multi-Agent Reasoner Synthesis (LangGraph Coordinator Panel) */}
      <section className="rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-wrap items-center justify-between gap-space-sm pb-space-sm">
          <div className="flex items-center gap-space-sm">
            <div className="p-2 rounded bg-surface-container text-secondary">
              <span className="material-symbols-outlined text-[20px]">hub</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">Multi-Agent Reasoner Synthesis</h2>
                <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-mono-data-sm text-[11px] font-medium">LangGraph Coordinator v2</span>
              </div>
              <span className="font-label-caps text-label-caps text-outline uppercase">
                COORDINATED GRAPH TRAVERSAL: DAG-7104 #{isNominal ? 'NOMINAL-PATH' : 'ANOMALY-ISOLATION-PATH'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded font-mono-data-sm text-[11px] font-semibold ${
                currentWindow.fusionDecision.isFallback
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  currentWindow.fusionDecision.isFallback ? "bg-amber-400" : "bg-emerald-400"
                }`}
              />
              {currentWindow.fusionDecision.isFallback
                ? `FALLBACK REASONER (${currentWindow.fusionDecision.reasonerModel || "mock"})`
                : `${(currentWindow.fusionDecision.reasonerProvider || "AI").toUpperCase()} REASONER (${currentWindow.fusionDecision.reasonerModel || "gpt-4o-mini"})`}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-low text-on-tertiary-container font-label-caps text-label-caps font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container"></span>
              SYNTHESIS VERIFIED // {currentWindow.groundingVerification.status}
            </span>
          </div>
        </div>

        {/* Fallback Warning Notice if applicable */}
        {currentWindow.fusionDecision.isFallback && currentWindow.fusionDecision.fallbackReason && (
          <div className="px-space-md py-2 rounded bg-amber-500/5 border border-amber-500/15 flex items-center justify-between gap-2 text-amber-300 font-mono-data-sm text-[11px]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px] text-amber-400">info</span>
              <span>
                <strong>Fallback Engaged:</strong> {currentWindow.fusionDecision.fallbackReason}
              </span>
            </div>
            <span className="text-on-surface-variant font-label-caps text-[10px] uppercase">
              Deterministic Mock Safe-State Active
            </span>
          </div>
        )}

        {/* Synthesized Explanation Card */}
        <div className="p-space-md rounded bg-surface-container-low text-on-surface flex flex-col gap-space-sm">
          <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase">
            <span>Generated Natural Language Explanation</span>
            <div className="flex items-center gap-3">
              <span className="font-mono-data-sm text-[11px] text-on-surface-variant">
                Latency: {currentWindow.fusionDecision.reasonerLatencyMs || 35}ms
              </span>
              <span className="font-mono-data-sm text-mono-data-sm">Confidence: {isNominal ? '99.88%' : '98.45%'}</span>
            </div>
          </div>
          <blockquote className="font-body-md text-body-md text-on-surface leading-relaxed italic">
            “{isNominal
              ? 'All four specialist agents report telemetry metrics well within expected variance. Power bus voltages and currents are nominal with solar array output matching orbital sunlight ephemeris. Thermal equilibrium on the payload deck is steady (+21.4°C). Attitude pointing rates confirm reaction wheels are stabilizing with zero drift. Communications RF carrier lock is solid with 0 packet loss. Fusion engine affirms nominal operational health.'
              : `${currentWindow.fusionDecision.explanationText} Calibrated stacking fusion model corroborates anomaly on affected subsystem. Automated isolation procedures recommended.`}”
          </blockquote>

          {/* Supporting Evidence Bullets */}
          {currentWindow.fusionDecision.supportingEvidence && currentWindow.fusionDecision.supportingEvidence.length > 0 && (
            <div className="p-3 rounded bg-surface-container-lowest/80 border border-surface-container mt-1">
              <div className="flex items-center gap-1.5 text-outline font-label-caps text-[11px] uppercase tracking-wider mb-1.5">
                <span className="material-symbols-outlined text-[14px] text-secondary">fact_check</span>
                <span>Supporting Diagnostic Evidence</span>
              </div>
              <ul className="space-y-1 font-mono-data-sm text-mono-data-sm text-on-surface-variant">
                {currentWindow.fusionDecision.supportingEvidence.map((ev, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-secondary select-none">•</span>
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Actionable Recommendations */}
          {currentWindow.fusionDecision.recommendations && currentWindow.fusionDecision.recommendations.length > 0 && (
            <div className="p-3 rounded bg-surface-container-lowest/80 border border-surface-container mt-1">
              <div className="flex items-center gap-1.5 text-outline font-label-caps text-[11px] uppercase tracking-wider mb-1.5">
                <span className="material-symbols-outlined text-[14px] text-tertiary">recommend</span>
                <span>Actionable Flight Operational Recommendations</span>
              </div>
              <ul className="space-y-1 font-body-sm text-body-sm text-on-surface">
                {currentWindow.fusionDecision.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-tertiary select-none font-bold">›</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-space-xs pt-1">
            <span className="font-label-caps text-label-caps text-outline uppercase mr-2">Telemetry Contracts Cited:</span>
            {currentWindow.fusionDecision.citedChannels.map((tag) => (
              <span key={tag} className="px-2 py-0.5 rounded bg-surface-container-lowest font-mono-data-sm text-mono-data-sm text-on-surface">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 4: Grounding Verification & Audit Integrity Section (Split 2-Columns) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-space-lg">
        {/* Grounding Verification Card */}
        <div className="rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col justify-between gap-space-md">
          <div className="flex flex-col gap-space-sm">
            <div className="flex items-center justify-between pb-space-xs">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-on-tertiary-container">fact_check</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">Grounding Verification</h3>
              </div>
              <span className="px-2.5 py-1 rounded bg-surface-container-low text-on-tertiary-container font-label-caps text-label-caps font-semibold">
                STATUS: {currentWindow.groundingVerification.status}
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Strict deterministic cross-reference validation ensuring reasoning nodes do not emit hallucinated channels or drift from raw telemetry contracts.
            </p>
            <div className="space-y-2 mt-2">
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">Retry Count:</span>
                <span className="font-semibold text-on-surface">{currentWindow.groundingVerification.retries} Retries (Pass on First Token Run)</span>
              </div>
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">Schema Validation:</span>
                <span className="inline-flex items-center gap-1 font-semibold text-on-tertiary-container">
                  <span className="material-symbols-outlined text-[14px]">check_circle</span>
                  PASS (Strict Pydantic JSON v2)
                </span>
              </div>
              <div className="p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm flex flex-col gap-1">
                <span className="font-label-caps text-label-caps text-outline uppercase">Reference Grounding Integrity Check</span>
                <span className="text-on-surface font-body-sm text-body-sm">
                  All {currentWindow.fusionDecision.citedChannels.length} cited telemetry channels map to verified physical telemetry contracts in SQLite database without hallucination or extraneous identifiers.
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase pt-space-xs">
            <span>Reasoner: {latestBackendResponse?.explanation?.llm_model || "Offline Rule-Based Reasoner (mock-reasoner)"}</span>
            <span className="text-on-surface font-mono">VERIFIER: services.verifier.grounding</span>
          </div>
        </div>

        {/* Audit Integrity Card */}
        <div className="rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col justify-between gap-space-md">
          <div className="flex flex-col gap-space-sm">
            <div className="flex items-center justify-between pb-space-xs">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-secondary">encrypted</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">Audit Trail &amp; Ledger Integrity</h3>
              </div>
              <span className="px-2 py-0.5 rounded bg-surface-container-low text-secondary font-label-caps text-label-caps font-semibold">
                {currentWindow.auditLog.status}
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Cryptographically hashed snapshot committed to the persistent SQLite operational ledger for post-flight auditability and blackbox replay.
            </p>
            <div className="space-y-2 mt-2">
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">Audit Entry ID:</span>
                <span className="font-semibold text-on-surface">{currentWindow.auditLog.entryId}</span>
              </div>
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">Decision ID:</span>
                <span className="font-semibold text-on-surface">{currentWindow.auditLog.decisionId}</span>
              </div>
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">Commit Status:</span>
                <span className="font-semibold text-on-surface">COMMITTED TO SQLITE</span>
              </div>
              <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low font-mono-data-sm text-mono-data-sm">
                <span className="text-on-surface-variant">SHA-256 Checksum:</span>
                <span className="font-mono font-semibold text-secondary truncate max-w-[200px]">
                  {currentWindow.auditLog.hash}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase pt-space-xs">
            <span>Timestamp (UTC):</span>
            <span className="text-on-surface font-mono">{currentWindow.timestamp}.412 UTC</span>
          </div>
        </div>
      </section>

      {/* SECTION 5: End-to-End Multi-Agent Incident Pipeline Timeline */}
      <section className="rounded-lg bg-surface-container-lowest p-space-lg shadow-sm flex flex-col gap-space-md">
        <div className="flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex flex-col">
            <span className="font-label-caps text-label-caps text-outline uppercase">Deterministic Pipeline Execution</span>
            <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">End-to-End Multi-Agent Orchestration Chain</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-on-tertiary-container"></span>
            <span className="font-mono-data-sm text-mono-data-sm text-on-surface font-medium">TOTAL CYCLE DURATION: 184ms</span>
          </div>
        </div>

        {/* Horizontal Linear Flow Pipeline Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-space-md pt-2">
          {/* Step 1: Ingestion */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 01</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Telemetry Ingestion</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                Window #{winNum} ingested. 15 raw channels demuxed &amp; validated.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.012 UTC
            </div>
          </div>

          {/* Step 2: Specialist Detection */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 02</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Specialist Detection</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                4/4 specialist agents evaluated. Anomaly scores computed in parallel.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.048 UTC
            </div>
          </div>

          {/* Step 3: Fusion Decision */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 03</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Fusion Decision</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                Deterministic rule corroboration applied. Level {isNominal ? '0' : '2'} verified.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.089 UTC
            </div>
          </div>

          {/* Step 4: Reasoner Explanation */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 04</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Reasoner Explanation</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                Synthesized natural language narrative generated from telemetry state.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.231 UTC
            </div>
          </div>

          {/* Step 5: Grounding Verification */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 05</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Grounding Verification</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                Zero hallucinations. Strict contract schema checks passed.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.364 UTC
            </div>
          </div>

          {/* Step 6: Audit Commit */}
          <div className="relative p-space-md rounded bg-surface-container-low flex flex-col justify-between h-44">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-outline uppercase">STEP 06</span>
                <span className="material-symbols-outlined text-[18px] text-on-tertiary-container">check_circle</span>
              </div>
              <span className="font-headline-sm text-[13px] font-bold text-on-surface">Audit Commit</span>
              <p className="font-body-sm text-[11px] text-on-surface-variant leading-tight mt-1">
                Immutable SQLite transaction committed with cryptographic digest.
              </p>
            </div>
            <div className="font-mono-data-sm text-[10px] text-on-surface font-mono p-1 rounded bg-surface-container-lowest">
              14:22:10.412 UTC
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
