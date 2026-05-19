# Risk & Exposure Intelligence Copilot

A professional demo repository for **Generative UI on Azure AI Foundry** with **Databricks Genie**, **CopilotKit**, and the **AG-UI protocol**.

The demo shows a conversational analytics experience where a user asks business questions, a Microsoft Foundry agent queries a Databricks Genie Space through MCP, and the web UI renders governed answers as controlled React components: KPIs, tables, bar charts, line/area trends, donut charts, and metric comparisons.

## Architecture

```text
Browser
  → Next.js + CopilotKit UI
  → /api/copilotkit
  → CopilotRuntime remote endpoint
  → FastAPI AG-UI/LangGraph bridge
  → Microsoft Foundry Prompt Agent
  → Databricks Genie MCP endpoint
  → Databricks SQL Warehouse + Unity Catalog demo view
```

See [docs/architecture.md](docs/architecture.md) for details.

## Repository layout

```text
apps/
  web/                 # Next.js + CopilotKit + controlled Generative UI components
  agent/               # FastAPI AG-UI bridge that invokes Microsoft Foundry
infra/                 # Azure Bicep for Databricks, ADLS Gen2, and monitoring
databricks/sql/        # Synthetic Risk Exposure demo dataset and business-facing view
scripts/               # Azure, Databricks, Genie, Foundry, validation, and cost-control scripts
docs/                  # Step-by-step setup, local runbook, demo script, and operations notes
.foundry/              # Local Foundry metadata template; real metadata is gitignored
```

## Getting started

1. **Deploy Azure and Databricks resources**
   Follow [docs/azure-setup.md](docs/azure-setup.md) to deploy the resource group, Databricks workspace, SQL Warehouse, demo data, Genie Space, Microsoft Foundry agent, and permissions.

2. **Run the AG-UI bridge and web app locally**
   Follow [docs/local-development.md](docs/local-development.md).

3. **Run the live demo**
   Use [docs/demo-script.md](docs/demo-script.md) for a guided session that validates conversational memory and rich visual components.

## Quick local run

After Azure/Databricks/Foundry setup is complete and `.foundry/agent-metadata.yaml` exists:

```bash
npm install
npm run install:agent

# terminal 1
npm run dev:agent

# terminal 2
npm run dev:web
```

Open <http://localhost:3000>.

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
- CopilotKit: <https://docs.copilotkit.ai/>
- AG-UI protocol: <https://docs.ag-ui.com/>
