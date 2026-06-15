# AGENTS.md

Root rules for AI agents and contributors. Read this before editing the repository.

## Project

- Demo: Generative UI for risk and exposure analytics, as a three-band spectrum (Controlled / Declarative / Open-Ended).
- Frontends: `apps/{controlled,declarative,open-ended}/web` use Next.js, React, CopilotKit, AG-UI, and Recharts.
- Agents: `apps/{controlled,declarative,open-ended}/agent` use FastAPI, LangGraph, and Azure AI Foundry (`main.py` local bridge / `hosted_main.py` Foundry Invocations, logic under `src/`). The controlled band also uses the Databricks Genie MCP.
- Infrastructure: `infra` Bicep; Databricks SQL demo data in `databricks/sql`.
- Scripts: `scripts` contains opt-in Azure/Databricks setup and cost-control commands.

## Hard rules

- Never commit secrets, live tokens, real tenant IDs, or local `.env` files.
- Keep Azure, Databricks, and Foundry calls opt-in; do not add live cloud calls to CI or pre-commit.
- Keep controlled UI component payloads deterministic and schema-shaped.
- Prefer small, typed, testable helpers over broad fallbacks or hidden behavior.
- Update README/docs when script names, setup flow, environment variables, or validation commands change.

## Commands

`<band>` is `controlled`, `declarative`, or `open-ended`.

- Install web dependencies (all workspaces): `npm install`.
- Install a band's Python agent + dev tools: `npm run install:<band>-agent`.
- Validate everything (3 agents + 3 webs — the CI gate): `npm run validate`.
- Validate one band: `npm run validate:<band>-agent` / `npm run validate:<band>-web`.
- Local dev: `npm run dev:<band>-agent` (local AG-UI bridge) and `npm run dev:<band>-web`; append `:hosted` to run the Foundry Invocations entrypoint instead.

## Validation expectations

- Python changes: run `npm run validate:<band>-agent` for the band(s) you touched.
- Frontend changes: run `npm run validate:<band>-web`.
- Script/docs setup changes: run `git diff --check` and validate referenced script names.
- Infrastructure changes: prefer `az deployment group what-if`; do not deploy without explicit user approval.

## Style

- Python: Ruff format/lint, typed functions, pytest coverage for parsing/mapping/session logic.
- TypeScript: strict types, no unnecessary `any`, keep component props explicit.
- Bash: `set -euo pipefail`, quote variables, use shared helpers in `scripts/lib/common.sh`.
- Comments: only for non-obvious behavior, external SDK quirks, or safety constraints.
