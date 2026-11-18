"use client";

import React, { ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { TelemetryProvider } from "../../context/TelemetryContext";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <TelemetryProvider>
      <div className="bg-surface font-body-md text-on-surface antialiased min-h-screen">
        <Header />
        <Sidebar />
        <div className="lg:pl-64">
          <main className="relative pt-36 min-h-screen bg-surface w-full px-margin-desktop py-space-lg">
            {children}
          </main>
        </div>
      </div>
    </TelemetryProvider>
  );
}
