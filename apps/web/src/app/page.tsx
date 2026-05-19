"use client";

import { useEffect, useRef, useState } from "react";
import { CopilotChat, useAgent, useCopilotKit } from "@copilotkit/react-core/v2";
import { DatabricksGenieMark } from "@/components/databricks-genie-mark";
import { DashboardStage, setDashboardLoading } from "@/components/generative-ui/dashboard-stage";
import { useRiskGenerativeUI } from "@/hooks/use-risk-generative-ui";

const suggestions = [
  { label: "Exposure by country", prompt: "What is the total exposure by country in 2026-Q2?" },
  { label: "Q1 vs Q2", prompt: "Compare exposure and overdue balance between 2026-Q1 and 2026-Q2." },
  { label: "Claims by broker", prompt: "Show me the brokers with the highest total claim amount." },
  { label: "Overdue risk", prompt: "Analyze overdue balance by risk class and highlight the main risks." },
];

export default function HomePage() {
  useRiskGenerativeUI();
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();
  const chatWrapRef = useRef<HTMLDivElement>(null);
  const [hasStartedChat, setHasStartedChat] = useState(false);

  useEffect(() => {
    const chatWrap = chatWrapRef.current;
    if (!chatWrap || hasStartedChat) return;

    const markStartedFromInput = (event: Event) => {
      const target = event.target;
      if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) {
        if (target.value.trim()) setHasStartedChat(true);
      }
    };

    chatWrap.addEventListener("input", markStartedFromInput, true);
    return () => chatWrap.removeEventListener("input", markStartedFromInput, true);
  }, [hasStartedChat]);

  const sendPrompt = (prompt: string) => {
    setHasStartedChat(true);
    setDashboardLoading();
    agent.addMessage({ id: crypto.randomUUID(), content: prompt, role: "user" });
    copilotkit.runAgent({ agent });
  };

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

      <section className="main-grid split-grid">
        <DashboardStage />

        <aside className="chat-card side-chat">
          <div className="chat-header">
            <div className="chat-brand">
              <DatabricksGenieMark compact animated />
              <span>Genie Risk Copilot</span>
            </div>
            <div className="live-indicator"><span /> Live</div>
          </div>
          <div className="suggestions">
            {suggestions.map(({ label, prompt }) => (
              <button className="suggestion" key={prompt} onClick={() => sendPrompt(prompt)}>
                {label}
              </button>
            ))}
          </div>
          <div className="chat-wrap" ref={chatWrapRef}>
            {!hasStartedChat && (
              <div className="chat-placeholder">
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
            )}
            <CopilotChat
              labels={{
                welcomeMessageText: " ",
                chatDisclaimerText: " ",
              }}
            />
          </div>
        </aside>
      </section>
    </main>
  );
}
