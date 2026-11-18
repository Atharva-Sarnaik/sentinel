"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetry } from "../../context/TelemetryContext";

export function Sidebar() {
  const pathname = usePathname();
  const { currentWindow } = useTelemetry();

  const feeds = [
    {
      label: "Telemetry Overview",
      href: "/overview",
      metric: `${currentWindow.cohesionIndex.toFixed(0)}%`,
      isGreen: true,
    },
    {
      label: "EPS Bus & Arrays",
      href: "/power",
      metric: `${currentWindow.subsystems.power.channels["P-1"]?.currentValue.toFixed(1)}V`,
      isGreen: currentWindow.subsystems.power.severity === "nominal",
    },
    {
      label: "Thermal Radiators",
      href: "/thermal",
      metric: `${currentWindow.subsystems.thermal.channels["T-1"]?.currentValue.toFixed(1)}°C`,
      isGreen: currentWindow.subsystems.thermal.severity === "nominal",
    },
    {
      label: "ADCS Gyros & RWA",
      href: "/attitude",
      metric: "0.02°/s",
      isGreen: currentWindow.subsystems.attitude.severity === "nominal",
    },
    {
      label: "S-Band / X-Band",
      href: "/communications",
      metric: "-82 dBm",
      isGreen: currentWindow.subsystems.communications.severity === "nominal",
    },
    {
      label: "AI Fusion Node",
      href: "/coordinator",
      metric: `${(100 - currentWindow.bayesianAnomalyProb * 100).toFixed(1)}%`,
      isGreen: currentWindow.fusionDecision.severity === "nominal",
    },
  ];

  return (
    <aside className="fixed left-0 top-36 bottom-0 w-64 bg-surface-container-lowest border-r border-surface-container z-40 hidden lg:flex flex-col justify-between p-space-md">
      <div className="flex flex-col gap-space-md">
        <div className="flex items-center justify-between px-space-sm pb-space-sm border-b border-surface-container">
          <span className="font-label-caps text-label-caps uppercase text-outline">Telemetry Feeds</span>
          <span className="font-label-caps text-label-caps px-1.5 py-0.5 rounded bg-surface-container text-on-surface font-semibold">
            6 ACTIVE
          </span>
        </div>

        <nav className="flex flex-col gap-1">
          {feeds.map((feed) => {
            const isActive = pathname === feed.href || (pathname === "/" && feed.href === "/overview");
            return (
              <Link
                key={feed.href}
                href={feed.href}
                className={`flex items-center justify-between px-space-sm py-2 rounded transition-colors ${
                  isActive
                    ? "bg-surface-container text-on-surface font-semibold"
                    : "text-body-sm font-body-sm text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
                }`}
              >
                <span>{feed.label}</span>
                <span
                  className={`font-mono-data-sm text-mono-data-sm ${
                    feed.isGreen ? "text-on-tertiary-container" : "text-error font-bold"
                  }`}
                >
                  {feed.metric}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Buffer Health Box */}
      <div className="p-space-sm rounded bg-surface-container-low border border-surface-container flex flex-col gap-1">
        <div className="flex items-center justify-between font-label-caps text-label-caps text-outline uppercase">
          <span>Buffer Health</span>
          <span>99.8%</span>
        </div>
        <div className="w-full h-1 bg-surface-container-highest rounded overflow-hidden">
          <div className="h-full bg-secondary w-full" />
        </div>
        <span className="font-mono-data-sm text-[10px] text-on-surface-variant mt-1">Frames: 8.24M / 0 Drop</span>
      </div>
    </aside>
  );
}
