# Architecture

## Goal

Show a cutting-edge Generative UI pattern for enterprise analytics: natural-language questions, governed data access, a Foundry agent, Databricks Genie, and controlled React visualizations streamed through AG-UI/CopilotKit.

## Runtime flow

1. The user interacts with the Next.js app.
2. CopilotKit sends the conversation to `/api/copilotkit`.
3. The Next.js route forwards the run to the FastAPI AG-UI bridge.
4. The bridge requests explicit human approval before governed data access.
5. After approval, the bridge invokes the Microsoft Foundry agent through the Foundry Responses API.
6. The Foundry agent uses a Databricks Genie MCP RemoteTool connection.
7. Genie queries the curated Unity Catalog view with a SQL Warehouse.
8. The bridge converts the answer/table into controlled component calls.
9. The UI renders KPIs, tables, charts, narrative cards, and follow-up actions.

## Key design choices

- The browser never calls Foundry or Databricks directly.
- Secrets and cloud credentials stay in the backend process.
- Financial/analytics visualizations are controlled React components, not arbitrary HTML from the model.
- Foundry conversation IDs are preserved so the agent can use previous Genie context.
- Local session context can answer simple follow-ups from the last returned table without a new Genie call.
- MCP approvals are handled after the user has approved governed data access in the UI.

## Main components

| Area | Path | Responsibility |
| --- | --- | --- |
| Web app | `apps/web` | Next.js, CopilotKit runtime route, chat shell, controlled UI components |
| Agent bridge | `apps/agent` | FastAPI, LangGraph/AG-UI, HITL approval, Foundry invocation, visualization mapping |
| Azure infra | `infra` | Databricks workspace, ADLS Gen2, Log Analytics |
| Databricks setup | `databricks/sql` and `scripts` | Demo data, SQL warehouse, Genie Space, permissions |
| Foundry setup | `scripts/60-setup-foundry-genie-agent.sh` | RemoteTool connection and Prompt Agent version |
