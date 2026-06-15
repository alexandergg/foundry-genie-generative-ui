# Band 01 · Controlled — Risk & Exposure Control Room

The flagship demo: governed analytics over **Databricks Genie** through **Microsoft Foundry**, rendered as **controlled Generative UI**. The agent can only invoke React components the developer registered (charts, tables, narrative cards) plus app-shell tools (`spotlightVisual`, `setPresentationMode`); it never generates markup.

| | |
| --- | --- |
| Web | `web/` — Next.js + CopilotKit v2 (<http://localhost:3000>) |
| Agent | `agent/` — LangGraph supervisor over AG-UI (<http://localhost:8123>) |
| Needs | Foundry project + prompt agent + Databricks Genie ([docs/azure-setup.md](../../docs/azure-setup.md)) |

## Run

```bash
npm run install:controlled-agent   # once
npm run dev:controlled-agent       # :8123 (local bridge; or point the web at the Hosted Agent)
npm run dev:controlled-web         # :3000
```

## How it works

1. Every turn goes through a **supervisor** (`agent/main.py`) that routes to `direct` (plain answer), `risk_data` (new governed Genie query) or `dashboard_op` (operate on what is already on screen).
2. Genie answers are parsed **deterministically** (`agent/src/visualization_mapper.py`) into pre-resolved tool-call pairs: `cacheDataset`, `addVisual`, `followUpQuestions`…
3. The frontend validates every payload with Zod before mutating its stores (`web/src/hooks/use-dashboard-tools.tsx`) and renders Recharts components. Process telemetry streams as AG-UI custom events into the status timeline.

## Key files

- `agent/main.py` — graph, routing, pre-resolved tool emission
- `agent/src/foundry_agent_client.py` — supervisor / dashboard-op / Genie prompts
- `web/src/hooks/use-dashboard-tools.tsx` + `web/src/hooks/dashboard-tools.ts` — tool bridges + schemas
- `web/src/components/generative-ui/` — the controlled component set and client stores
- `agent/hosted_main.py` + `agent/Dockerfile` + `agent/agent.yaml` — Foundry Hosted Agent packaging

More: [docs/generative-ui-spectrum.md](../../docs/generative-ui-spectrum.md) · [docs/architecture.md](../../docs/architecture.md) · [docs/demo-script.md](../../docs/demo-script.md)
