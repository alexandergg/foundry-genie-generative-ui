# Risk & Exposure Intelligence Copilot

A professional demo repository for **Generative UI on Azure AI Foundry** with **Databricks Genie**, **CopilotKit**, and the **AG-UI protocol**.

The demo shows a conversational analytics experience where a user asks business questions, a Microsoft Foundry agent queries a Databricks Genie Space through MCP, and the web UI renders governed answers as controlled React components: KPIs, tables, bar charts, line/area trends, donut charts, and metric comparisons.

## Architecture

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

## Repository layout

```text
apps/
  web/                 # Next.js + CopilotKit + controlled Generative UI components
  agent/               # AG-UI/LangGraph bridge plus Foundry Hosted Agent invocations entrypoint
infra/                 # Azure Bicep for Foundry, Key Vault, ACR, monitoring, and optional Databricks
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

3. **Run the frontend locally**
   Follow [docs/local-development.md](docs/local-development.md) to configure `apps/web/.env.local`, authenticate with Azure CLI, and start the Next.js app.

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
