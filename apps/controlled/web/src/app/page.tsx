"use client";

import { useSyncExternalStore } from "react";
import { CopilotSidebar, useConfigureSuggestions } from "@copilotkit/react-core/v2";
import { DatabricksGenieMark } from "@/components/databricks-genie-mark";
import { DashboardStage } from "@/components/generative-ui/dashboard-stage";
import { getViewSnapshot, subscribeView } from "@/components/generative-ui/view-store";
import { useRiskGenerativeUI } from "@/hooks/use-risk-generative-ui";
import { useRiskUiEvents } from "@/hooks/use-risk-ui-events";
import { useDashboardReadable } from "@/hooks/use-dashboard-readable";
import { useDashboardTools } from "@/hooks/use-dashboard-tools";

const SIDEBAR_WIDTH = 460;

// Spectrum nav targets: NEXT_PUBLIC_* values are inlined at build time, so set
// them when building for a deployed environment; localhost works out of the box.
const SPECTRUM_URLS = {
  controlled: process.env.NEXT_PUBLIC_SPECTRUM_URL_CONTROLLED ?? "http://localhost:3000",
  declarative: process.env.NEXT_PUBLIC_SPECTRUM_URL_DECLARATIVE ?? "http://localhost:3001",
  openEnded: process.env.NEXT_PUBLIC_SPECTRUM_URL_OPEN_ENDED ?? "http://localhost:3002",
};

const starterSuggestions = [
  { title: "Exposure by country", message: "What is the total exposure by country in 2026-Q2?" },
  { title: "Q1 vs Q2", message: "Compare exposure and overdue balance between 2026-Q1 and 2026-Q2." },
  { title: "Claims by broker", message: "Show me the brokers with the highest total claim amount." },
  { title: "Overdue risk", message: "Analyze overdue balance by risk class and highlight the main risks." },
];

function GenieWelcomeMessage() {
  return (
    <div className="genie-welcome-message">
      <div className="chat-intro-logo">
        <DatabricksGenieMark animated />
      </div>
      <p>Start with a governed risk question.</p>
      <div className="chat-intro-pulses" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default function HomePage() {
  useRiskGenerativeUI();
  useRiskUiEvents();
  useDashboardReadable();
  useDashboardTools();
  useConfigureSuggestions({ suggestions: starterSuggestions, available: "before-first-message" }, []);
  const view = useSyncExternalStore(subscribeView, getViewSnapshot, getViewSnapshot);

  return (
    <main className={view.presentationMode ? "shell presentation-mode" : "shell"}>
      <section className="hero minimal-hero">
        <div className="hero-copy">
          <DatabricksGenieMark animated />
          <div>
            <p className="eyebrow band-eyebrow">Generative UI spectrum · Band 01</p>
            <h1 className="band-title">
              Risk <em>Intelligence</em>
            </h1>
          </div>
        </div>
        <aside className="hero-side">
          <nav className="spectrum-nav" aria-label="Generative UI spectrum demos">
            <a href={SPECTRUM_URLS.controlled} aria-current="page" className="current">
              <b>01</b> Controlled
            </a>
            <a href={SPECTRUM_URLS.declarative}>
              <b>02</b> Declarative
            </a>
            <a href={SPECTRUM_URLS.openEnded}>
              <b>03</b> Open-Ended
            </a>
          </nav>
          <div className="status-pillbar" aria-label="Demo stack">
            <span>Foundry</span>
            <span>Genie</span>
            <span>AG-UI</span>
          </div>
        </aside>
      </section>

      <section className="main-grid">
        <DashboardStage />
      </section>

      <CopilotSidebar
        defaultOpen
        width={SIDEBAR_WIDTH}
        labels={{
          modalHeaderTitle: "Genie Risk Copilot",
          chatInputPlaceholder: "Ask about exposure, claims, brokers, or overdue risk…",
          chatDisclaimerText: " ",
          welcomeMessageText: "Start with a governed risk question.",
        }}
        messageView={{
          cursor: () => <span className="chat-cursor" aria-label="Assistant is responding" />,
        }}
        welcomeScreen={{ welcomeMessage: GenieWelcomeMessage }}
      />
    </main>
  );
}
