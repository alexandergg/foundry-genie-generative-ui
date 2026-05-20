"use client";

import { useState } from "react";
import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2";
import type { McpApprovalCardProps } from "./types";

export function McpApprovalCard({
  requestId,
  question,
  dataSource,
  purpose,
  approvalCommand,
  rejectCommand,
  reviseCommandPrefix,
  expiresAt,
  auditId,
}: McpApprovalCardProps) {
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();
  const [revisedQuestion, setRevisedQuestion] = useState(question);

  const submitCommand = (content: string) => {
    agent.addMessage({ id: crypto.randomUUID(), content, role: "user" });
    copilotkit.runAgent({ agent });
  };

  const approve = () => submitCommand(approvalCommand);
  const reject = () => submitCommand(rejectCommand ?? `reject ${requestId}`);
  const approveRevision = () => {
    const trimmed = revisedQuestion.trim();
    if (!trimmed) return;
    submitCommand(`${reviseCommandPrefix ?? `revise ${requestId}:`} ${trimmed}`);
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
        {auditId ? <div><dt>Audit</dt><dd>{auditId}</dd></div> : null}
        {expiresAt ? <div><dt>Expires</dt><dd>{new Date(expiresAt).toLocaleString()}</dd></div> : null}
      </dl>
      <label className="approval-revision">
        <span>Revise question before approval</span>
        <textarea value={revisedQuestion} onChange={(event) => setRevisedQuestion(event.target.value)} rows={3} />
      </label>
      <div className="approval-actions">
        <button className="approval-button" onClick={approve}>Approve and query Genie</button>
        <button className="approval-button secondary" onClick={approveRevision}>Approve revised question</button>
        <button className="approval-button danger" onClick={reject}>Reject</button>
      </div>
    </div>
  );
}
