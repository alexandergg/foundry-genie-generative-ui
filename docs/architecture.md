# Architecture

## Goal

Show a cutting-edge Generative UI pattern for enterprise analytics: natural-language questions, governed data access, a Foundry agent, Databricks Genie, and controlled React visualizations streamed through AG-UI/CopilotKit.

## Runtime flow

1. The user interacts with the Next.js app.
2. CopilotKit sends the conversation to `/api/copilotkit`; the browser never calls Foundry directly.
3. The Next.js route uses an AG-UI `HttpAgent` and forwards the run to either the local FastAPI endpoint or a Microsoft Foundry Hosted Agent Invocations endpoint.
4. The AG-UI/LangGraph supervisor routes the request to either a direct response, a dashboard operation on cached data, or a governed Genie query.
5. For governed queries the runtime invokes the Microsoft Foundry prompt agent through the Foundry Responses API.
6. The Foundry prompt agent uses a Databricks Genie MCP RemoteTool connection.
7. Genie queries the curated Unity Catalog view with a SQL Warehouse.
8. The AG-UI/LangGraph runtime converts the answer/table into controlled component calls and attaches visual provenance.
9. The UI renders tables, charts, narrative cards, follow-up actions, and a semantic run timeline.
10. Foundry writes prompt-agent, hosted-agent, model, and dependency telemetry to the connected workspace-based Application Insights resource for trace analysis.

## Key design choices

- The browser never calls Foundry or Databricks directly; `/api/copilotkit` remains the web boundary.
- Secrets and cloud credentials stay in backend processes. For hosted endpoints, the Next.js route can use server-side Azure identity to call Foundry Invocations.
- AG-UI stays as the UI protocol because it is purpose-built for streaming agent UI, state, and controlled component rendering.
- The dashboard keeps a semantic timeline for planning, querying, normalization, rendering, completion, and safe errors.
- The local FastAPI endpoint and hosted Invocations entrypoint share the same LangGraph behavior to avoid divergent demo logic.
- Financial/analytics visualizations are controlled React components, not arbitrary HTML from the model.
- Foundry conversation IDs are preserved so the agent can use previous Genie context.
- Local session context can answer simple follow-ups from the last returned table without a new Genie call.
- The Genie MCP tool is registered in Foundry with `require_approval: never`, so MCP tool calls execute without per-call approval rounds.
- Provenance is captured once per Genie result on the cached dataset (`source`, `generatedAt`, `traceId`, `rowCount`, and normalization warnings); every visual derived from that dataset inherits it and stamps its own `visualId` when rendering the footer.
- Application Insights is connected at both Foundry account and project scopes so prompt-agent and hosted-agent traces are visible from Foundry Traces and Azure Monitor.

## Main components

| Area | Path | Responsibility |
| --- | --- | --- |
| Web app | `apps/web` | Next.js, CopilotKit runtime route, chat shell, controlled UI components |
| Agent runtime | `apps/agent` | Local FastAPI AG-UI endpoint, Foundry Hosted Agent Invocations entrypoint, LangGraph supervisor routing, Foundry invocation, visualization mapping |
| Azure infra | `infra` | Optional Databricks workspace, ADLS Gen2, Microsoft Foundry project/model deployment, Key Vault, managed identity, Azure Container Registry, Log Analytics, Application Insights, Foundry tracing connections |
| Databricks setup | `databricks/sql` and `scripts` | Demo data, SQL warehouse, Genie Space, permissions |
| Foundry setup | `scripts/setup-foundry-genie-agent.sh` | RemoteTool connection and Prompt Agent version |

## Azure-native hosted agent path

The recommended cloud shape keeps CopilotKit/AG-UI for the web experience, but runs the custom AG-UI/LangGraph runtime as a **Microsoft Foundry Hosted Agent** using the **Invocations** protocol. The hosted entrypoint is `apps/agent/hosted_main.py`; local development can continue to use `main.py` and FastAPI on port 8123.

Foundry Hosted Agents provide the Azure-managed container endpoint, lifecycle, identity, and telemetry boundary for custom agent code. Invocations is used instead of the Responses protocol because AG-UI is a custom streaming UI protocol and the runtime must emit deterministic component/tool events.

## Observability

The Bicep deployment creates a Log Analytics workspace and workspace-based Application Insights component, then adds `AppInsights` connections at both the Foundry account and project scopes. This makes the prompt Genie agent, hosted AG-UI agent, model calls, and agent dependencies available in Foundry Traces and Azure Monitor. Foundry tracing is generally available for prompt agents; hosted/custom agent tracing is currently documented by Microsoft as preview.

Useful telemetry tables include `AppRequests` for hosted-agent invocations, `AppDependencies` for prompt-agent/model calls, `AppTraces` for runtime logs, and `AppGenAIContent` for GenAI content events. Treat trace data as production telemetry: do not send secrets in prompts, tool inputs, or span attributes, and control access with Log Analytics/Application Insights RBAC.
