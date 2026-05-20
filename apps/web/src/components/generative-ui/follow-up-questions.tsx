"use client";

import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2";
import { setDashboardPlanning } from "./dashboard-store";
import type { FollowUpQuestionsProps } from "./types";

export function FollowUpQuestions({ title, questions }: FollowUpQuestionsProps) {
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();

  const ask = (question: string) => {
    setDashboardPlanning({
      approach: "Run a drill-down on the previous result and refresh the visual canvas.",
      technology: "Azure AI Foundry + Databricks Genie + AG-UI",
      key_elements: ["follow-up", "real query", "new chart"],
    });
    agent.addMessage({ id: crypto.randomUUID(), content: question, role: "user" });
    copilotkit.runAgent({ agent });
  };

  return (
    <div className="viz-card followup-card">
      <p className="eyebrow">Next analyses</p>
      <h3 className="viz-title">{title}</h3>
      <div className="followup-grid">
        {questions.map((question) => (
          <button className="followup-button" key={question} onClick={() => ask(question)}>
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
