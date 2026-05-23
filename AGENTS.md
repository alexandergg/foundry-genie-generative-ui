# AGENTS.md

Root rules for AI agents and contributors. Read this before editing the repository.

## Project

- Demo: Generative UI for risk and exposure analytics.
- Frontend: `apps/web` uses Next.js, React, CopilotKit, AG-UI, and Recharts.
- Agent: `apps/agent` uses FastAPI, LangGraph, Azure AI Foundry, and Databricks Genie MCP.
- Infrastructure: `infra` Bicep; Databricks SQL demo data in `databricks/sql`.
- Scripts: `scripts` contains opt-in Azure/Databricks setup and cost-control commands.

## Hard rules

- Never commit secrets, live tokens, real tenant IDs, or local `.env` files.
- Keep Azure, Databricks, and Foundry calls opt-in; do not add live cloud calls to CI or pre-commit.
- Keep controlled UI component payloads deterministic and schema-shaped.
- Prefer small, typed, testable helpers over broad fallbacks or hidden behavior.
- Update README/docs when script names, setup flow, environment variables, or validation commands change.

## Commands

- Install frontend dependencies: `npm install`.
- Install the Python agent and dev tools: `npm run install:agent`.
- Run everything locally: `npm run validate`.
- Agent-only validation: `npm run validate:agent`.
- Web validation: `npm run validate:web`.
- Local dev: `npm run dev:agent` and `npm run dev:web`.

## Validation expectations

- Python changes: run `npm run validate:agent`.
- Frontend changes: run `npm run validate:web`.
- Script/docs setup changes: run `git diff --check` and validate referenced script names.
- Infrastructure changes: prefer `az deployment group what-if`; do not deploy without explicit user approval.

## Style

- Python: Ruff format/lint, typed functions, pytest coverage for parsing/mapping/session logic.
- TypeScript: strict types, no unnecessary `any`, keep component props explicit.
- Bash: `set -euo pipefail`, quote variables, use shared helpers in `scripts/lib/common.sh`.
- Comments: only for non-obvious behavior, external SDK quirks, or safety constraints.
