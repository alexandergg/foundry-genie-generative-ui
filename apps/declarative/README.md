# Band 02 · Declarative — A2UI over a custom component catalog

The middle of the spectrum (course L4): the app defines a **component catalog** (`copilotkit://risk-catalog` — `Metric` with trends, Recharts `BarChart`/`PieChart`, `DashboardCard`, `DataTable`, `Badge`…) and the agent composes interfaces against it in **both A2UI schema styles**:

- **Fixed** (`executive` / `brief`): pre-authored layouts executed by a real LangGraph `ToolNode`. Deterministic — works with **no model at all** thanks to a keyword-fallback planner.
- **Dynamic** (`freeform`): the LLM assembles the layout itself via the injected `render_a2ui` tool, rendered progressively as it streams.

| | |
| --- | --- |
| Web | `web/` — catalog definitions + renderers, CopilotKit v2 chat (<http://localhost:3001>) |
| Agent | `agent/` — planner + fixed layouts + dynamic compose node (<http://localhost:8124>) |
| Needs | A Foundry model endpoint only (`RISK_MODEL_ENDPOINT`) — no Databricks |

## Run

```bash
cp agent/.env.example agent/.env    # set RISK_MODEL_ENDPOINT (+ deployment)
npm run install:declarative-agent   # once
npm run dev:declarative-agent       # :8124
npm run dev:declarative-web         # :3001
```

## Key files

- `web/src/catalog/definitions.ts` — the catalog **contract** the agent reads (Zod)
- `web/src/catalog/renderers.tsx` — the React/Recharts implementations (`createCatalog`)
- `agent/src/report_catalog.py` — pre-authored fixed layouts (contract-tested in CI)
- `agent/src/planner.py` — layout/quarter/summary planner with offline fallback
- `agent/src/graph.py` — the dual-mode graph (ToolNode + dynamic streaming node)
- `agent/hosted_main.py` + `agent/Dockerfile` + `agent/agent.yaml` — Foundry Hosted Agent packaging

Try, in order: `Give me the executive risk report for 2026-Q2` → `Show the compact risk brief for 2026-Q1 instead` → `Compose a risk dashboard your way — pick the catalog components you think fit best`.

More: [docs/generative-ui-spectrum.md](../../docs/generative-ui-spectrum.md) · session prompts in [docs/session-guide.es.md](../../docs/session-guide.es.md)
