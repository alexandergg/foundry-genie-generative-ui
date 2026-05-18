"use client";

import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2";
import type { McpApprovalCardProps } from "./types";

export function McpApprovalCard({ requestId, question, dataSource, purpose, approvalCommand }: McpApprovalCardProps) {
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();

  const approve = () => {
    agent.addMessage({ id: crypto.randomUUID(), content: approvalCommand, role: "user" });
    copilotkit.runAgent({ agent });
  };

  return (
    <div className="viz-card approval-card">
      <p className="eyebrow">Human-in-the-loop approval</p>
      <h3 className="viz-title">Authorize governed data access</h3>
      <p className="viz-muted approval-intro">The agent wants to query Databricks Genie before answering.</p>
      <dl className="approval-details">
        <div><dt>Source</dt><dd>{dataSource}</dd></div>
        <div><dt>Purpose</dt><dd>{purpose}</dd></div>
        <div><dt>Question</dt><dd>{question}</dd></div>
        <div><dt>Request</dt><dd>{requestId}</dd></div>
      </dl>
      <button className="approval-button" onClick={approve}>Approve and query Genie</button>
    </div>
  );
}
