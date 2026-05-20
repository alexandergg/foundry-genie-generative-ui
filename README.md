# Risk & Exposure Intelligence Copilot

A professional demo repository for **Generative UI on Azure AI Foundry** with **Databricks Genie**, **CopilotKit**, and the **AG-UI protocol**.

The demo shows a conversational analytics experience where a user asks business questions, a Microsoft Foundry agent queries a Databricks Genie Space through MCP, and the web UI renders governed answers as controlled React components: KPIs, tables, bar charts, line/area trends, donut charts, and metric comparisons.

## Generative UI approach

CopilotKit describes Generative UI as a spectrum from developer-controlled components to fully agent-generated interfaces. This demo intentionally uses **Controlled Generative UI**, the most predictable band of that spectrum.

In Controlled Generative UI, developers ship a fixed set of pre-built components and register them with the agent. At runtime, the agent chooses which component to render and supplies typed data for that component, but it cannot invent arbitrary markup, layouts, or visual surfaces. In this repository, the registered components include KPI strips, chart cards, narrative cards, approval cards, follow-up questions, and insight tables.

That model fits this demo because risk and exposure analytics need governed data access, deterministic visual payloads, and repeatable executive-facing UI. The agent can still make the experience feel dynamic by selecting the right visual for each business question, while the frontend keeps control over rendering, styling, validation, and user approval flows.

This is different from other bands in the CopilotKit Generative UI Spectrum:

- **Declarative Generative UI:** the agent assembles a UI tree from a catalog of smaller building blocks. This demo does not currently expose a composable A2UI-style component catalog.
- **MCP Apps:** a third-party app surface is embedded, typically in a sandboxed iframe. This demo uses MCP for Databricks Genie access, but the UI components are first-party React components, not embedded MCP applets.
- **Fully Open Generative UI:** the agent generates custom HTML, SVG, or a remote UI surface at runtime. This demo avoids that mode to keep analytics output predictable and on-brand.

See CopilotKit's [Generative UI Spectrum](https://www.copilotkit.ai/generative-ui-spectrum) for the taxonomy behind this design choice. The architecture is also available as an editable diagrams.net file: [docs/generative-ui-architecture.drawio](docs/generative-ui-architecture.drawio).

## Architecture

<p align="center">
  <img src="docs/assets/azure-architecture-overview.png" alt="High-level Azure architecture for the Risk & Exposure Intelligence Copilot" width="100%">
</p>

The diagram above shows the high-level Azure implementation: a controlled CopilotKit UI calls the hosted AG-UI agent in Microsoft Foundry, which coordinates governed analytics through a Foundry prompt agent and Databricks Genie MCP. Identity, secrets, container image delivery, and telemetry stay in managed Azure services.

```text
Browser
  → Next.js + CopilotKit UI
  → /api/copilotkit
  → CopilotRuntime + AG-UI HttpAgent
  → Local FastAPI AG-UI bridge or Foundry Hosted Agent invocations endpoint
  → LangGraph HITL + controlled UI mapping
  → Microsoft Foundry Prompt Agent
  → Databricks Genie MCP endpoint
  → Databricks SQL Warehouse + Unity Catalog demo view
  → Application Insights + Foundry Traces for prompt and hosted agent telemetry
```

See [docs/architecture.md](docs/architecture.md) for details.

## Microsoft Foundry implementation

The deployed Foundry project uses a two-agent design:

| Agent | Type | Responsibility |
| --- | --- | --- |
| `risk-exposure-ag-ui-hosted` | Hosted Agent, Invocations protocol | Runs the custom AG-UI/LangGraph runtime, handles human approval, session orchestration, controlled UI events, and telemetry. |
| `risk-exposure-genie-agent` | Prompt Agent | Encapsulates governed Databricks Genie access through a Foundry MCP tool and the deployed model. |

This separation keeps the UI orchestration and the governed analytics tool boundary explicit. CopilotKit talks to the AG-UI runtime; the runtime coordinates approval and invokes the Genie-backed prompt agent only when business data is needed. Both agents are visible in Foundry with sessions, traces, monitor metrics, and versioned deployment metadata.

<details>
<summary>Foundry portal walkthrough</summary>

| Portal view | What it demonstrates |
| --- | --- |
| <img src="docs/assets/foundry-agents-list.png" alt="Foundry agents list" width="360"> | The project contains the hosted AG-UI runtime agent and the Databricks Genie prompt agent. |
| <img src="docs/assets/foundry-hosted-agent-playground.png" alt="Hosted agent playground" width="360"> | The hosted agent uses the Invocations protocol and a packaged code asset. |
| <img src="docs/assets/foundry-hosted-agent-sessions.png" alt="Hosted agent sessions" width="360"> | Foundry records hosted-agent sessions for operational inspection. |
| <img src="docs/assets/foundry-hosted-agent-traces.png" alt="Hosted agent traces" width="360"> | Invocation traces capture completion status and latency for the AG-UI runtime. |
| <img src="docs/assets/foundry-hosted-agent-monitor.png" alt="Hosted agent monitor" width="360"> | Monitor views expose agent runs, tool-call activity, and operational metrics. |
| <img src="docs/assets/foundry-genie-agent-tool.png" alt="Genie prompt agent with tool" width="360"> | The prompt agent is configured with domain instructions and a Databricks Genie MCP tool. |
| <img src="docs/assets/foundry-tools-list.png" alt="Foundry tools list" width="360"> | The Databricks Genie integration is registered as a Foundry MCP tool. |
| <img src="docs/assets/foundry-databricks-genie-mcp-tool.png" alt="Databricks Genie MCP tool" width="360"> | The MCP tool is authenticated through Foundry project managed identity and used by the prompt agent. |
| <img src="docs/assets/foundry-model-deployment.png" alt="Foundry model deployment" width="360"> | The Foundry model deployment is versioned and uses token-based Azure authentication rather than API keys. |

</details>

## Repository layout

```text
apps/
  web/                 # Next.js + CopilotKit + controlled Generative UI components
  agent/               # AG-UI/LangGraph bridge plus Foundry Hosted Agent invocations entrypoint
infra/                 # Azure Bicep for Foundry, Key Vault, ACR, monitoring, optional Databricks, and optional frontend App Service
databricks/sql/        # Synthetic Risk Exposure demo dataset and business-facing view
scripts/               # Azure, Databricks, Genie, Foundry, validation, and cost-control scripts
docs/                  # Step-by-step setup, local runbook, demo script, and operations notes
.foundry/              # Local Foundry metadata template; real metadata is gitignored
```

## Getting started

This is a **live Azure demo**, not an offline mock. The frontend can run locally, but useful answers require a deployed Microsoft Foundry prompt agent connected to Databricks Genie. You can then choose whether the custom AG-UI/LangGraph runtime runs locally or as a Foundry Hosted Agent.

1. **Deploy the cloud foundation**
   Follow [docs/azure-setup.md](docs/azure-setup.md) through validation step 9. This creates the Microsoft Foundry project/model, Key Vault, ACR, Application Insights tracing connections, and the Foundry prompt agent. Configure `infra/main.demo.bicepparam` to reuse your existing Databricks Genie workspace or to deploy a new one.

2. **Choose a runtime path**
   - **Recommended demo path:** deploy the AG-UI runtime as a Foundry Hosted Agent, then run only the frontend locally.
   - **Developer path:** run the AG-UI/FastAPI bridge locally; it still calls the deployed Foundry prompt agent and Databricks Genie.

3. **Run or deploy the frontend**
   Follow [docs/local-development.md](docs/local-development.md) to configure `apps/web/.env.local`, authenticate with Azure CLI, and start the Next.js app. If you want the frontend hosted in Azure too, enable the optional App Service resource in `infra/main.demo.bicepparam` and follow [docs/azure-setup.md](docs/azure-setup.md#11-optional-deploy-the-nextjs-frontend-to-azure-app-service).

4. **Run the live demo**
   Use [docs/demo-script.md](docs/demo-script.md) for a guided session that validates approval, conversational memory, traces, and rich visual components.

## Quick local frontend run

After cloud setup is complete and you have a Foundry Hosted Agent Invocations endpoint:

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
```

Set these values in `apps/web/.env.local`:

```bash
AG_UI_AGENT_URL="https://<hosted-agent-invocations-endpoint>"
AG_UI_AGENT_AUTH="azure-identity"
AG_UI_AGENT_SCOPE="https://ai.azure.com/.default"
```

Then run:

```bash
az login
npm run dev:web
```

Open <http://localhost:3000>. For the local FastAPI bridge alternative, see [docs/local-development.md](docs/local-development.md#run-with-the-local-ag-ui-bridge).

## Validation

```bash
npm run validate
```

This runs Python Ruff formatting/lint checks, mypy, pytest, Python compilation, and the frontend lint/build pipeline. See [CONTRIBUTING.md](CONTRIBUTING.md) for pre-commit setup.

## Cost control

The demo is intentionally live: there is no mock runtime. Databricks SQL Warehouse usage can incur cost. Stop compute after each session:

```bash
source .risk.env.local
./scripts/stop-compute.sh
./scripts/validate-risk.sh
```

See [docs/cost-control.md](docs/cost-control.md).

## Official references

- Databricks Genie setup: <https://learn.microsoft.com/azure/databricks/genie/set-up>
- Databricks Genie API: <https://learn.microsoft.com/azure/databricks/genie/conversation-api>
- Microsoft Foundry MCP tools: <https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol>
- Foundry hosted agents quickstart: <https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent>
- Foundry hosted agent runtime components: <https://learn.microsoft.com/azure/ai-foundry/agents/concepts/runtime-components?view=foundry>
- Foundry tracing with Application Insights: <https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup>
- CopilotKit: <https://docs.copilotkit.ai/>
- AG-UI protocol: <https://docs.ag-ui.com/>
