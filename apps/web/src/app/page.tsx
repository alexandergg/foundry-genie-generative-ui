"use client";

import { CopilotSidebar, useConfigureSuggestions } from "@copilotkit/react-core/v2";
import { DatabricksGenieMark } from "@/components/databricks-genie-mark";
import { DashboardStage } from "@/components/generative-ui/dashboard-stage";
import { useRiskGenerativeUI } from "@/hooks/use-risk-generative-ui";
import { useRiskUiEvents } from "@/hooks/use-risk-ui-events";
import { useDashboardReadable } from "@/hooks/use-dashboard-readable";
import { useDashboardTools } from "@/hooks/use-dashboard-tools";

const SIDEBAR_WIDTH = 460;

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

  return (
    <main className="shell">
      <section className="hero minimal-hero">
        <div className="hero-copy">
          <DatabricksGenieMark animated />
          <div>
            <p className="eyebrow">Foundry + Genie</p>
            <h1>Risk Intelligence</h1>
          </div>
        </div>
        <aside className="status-pillbar" aria-label="Demo stack">
          <span>Foundry</span>
          <span>Genie</span>
          <span>HITL</span>
          <span>AG-UI</span>
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
