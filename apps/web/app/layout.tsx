import type { Metadata } from "next";
import "./globals.css";
import { Shell } from "../components/layout/Shell";

export const metadata: Metadata = {
  title: "SENTINEL — Aerospace Mission Control",
  description:
    "Multi-Agent AI System for Satellite Telemetry Health Monitoring and Anomaly Detection — Decision-support mission control dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
        />
      </head>
      <body className="bg-surface font-body-md text-on-surface antialiased">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
