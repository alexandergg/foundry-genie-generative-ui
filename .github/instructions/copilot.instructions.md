---
applyTo: "**"
---

# Repository instructions

Use these instructions for all work in this repository.

- This is a Generative UI demo for Azure AI Foundry + Databricks Genie + CopilotKit/AG-UI.
- Do not invent mock cloud behavior for production paths; live Foundry/Databricks calls must remain explicit and opt-in.
- Never print or commit secrets from `.env`, `.env.local`, `.risk.env.local`, or `.foundry/agent-metadata.yaml`.
- Keep validation commands current in `README.md`, `docs/`, `AGENTS.md`, and CI.
- Prefer small, typed, behavior-tested changes over broad rewrites.
- After changing Python, run `npm run validate:agent`.
- After changing frontend code, run `npm run validate:web`.
- After changing scripts or docs, run `git diff --check` and verify script references.
