# The Generative UI Spectrum in This Repository

This repository now ships **three runnable demos, one per band of the Generative UI spectrum** popularized by CopilotKit and the DeepLearning.AI course [Build Interactive Agents with Generative UI](https://www.deeplearning.ai/courses/build-interactive-agents-with-generative-ui): **Controlled**, **Declarative (A2UI)**, and **Open-Ended**. All three share the same stack — a Python LangGraph agent exposed over the **AG-UI protocol**, a Next.js frontend on **CopilotKit v2**, and Azure AI Foundry models — so the only variable between demos is *who decides what the UI looks like*.

## The three bands at a glance

| Band | Who authors the UI | What the agent decides | Demo apps | Ports | External dependencies |
| --- | --- | --- | --- | --- | --- |
| **Controlled** | Developer ships React components | Which component to render, with which typed data | `apps/controlled/web` + `apps/controlled/agent` | 3000 / 8123 | Foundry project + Databricks Genie |
| **Declarative** | Developer defines a component **catalog**; layouts are pre-authored (fixed schema) or agent-assembled (dynamic schema) | Which layout/data (fixed) or the whole composition within the catalog (dynamic) | `apps/declarative/web` + `apps/declarative/agent` | 3001 / 8124 | Foundry model endpoint only |
| **Open-Ended** | Nobody — the agent writes sandboxed HTML/CSS/JS or launches full MCP Apps | Everything, bounded only by the tools' contracts | `apps/open-ended/web` + `apps/open-ended/agent` | 3002 / 8125 | Foundry model endpoint (+ internet for MCP Apps) |

The three demos can run simultaneously, so a live session can switch bands without restarting anything.

## Band 1 — Controlled (`apps/controlled/web` + `apps/controlled/agent`)

The agent emits **pre-resolved tool-call pairs** (`_component_message` in `apps/controlled/agent/main.py`): an `AIMessage` carrying a tool call such as `addVisual`, immediately followed by its `ToolMessage` result. The frontend registers a `useRenderTool` bridge per tool (`apps/controlled/web/src/hooks/use-dashboard-tools.tsx`) that validates the raw args with Zod (`apps/controlled/web/src/hooks/dashboard-tools.ts`) and mutates client-side stores; `DashboardStage` renders the Recharts components.

Key properties:

- The agent can only invoke components from a fixed allowlist (`apps/controlled/agent/src/component_registry.py`).
- Args are schema-validated on the client before any mutation — malformed or mid-stream payloads are skipped.
- The agent also drives the *app shell*, not just the chat: `spotlightVisual` highlights one visual and dims the rest, and `setPresentationMode` hides the chrome for presenting (`apps/controlled/web/src/components/generative-ui/view-store.ts`). These travel through the same controlled tool path as every other dashboard operation.
- Streaming process telemetry uses AG-UI custom events (`risk_ui_event`) rendered as a status timeline.

Run it:

```bash
npm run dev:controlled-agent   # FastAPI AG-UI bridge on :8123 (or use the Foundry Hosted Agent)
npm run dev:controlled-web     # Next.js on :3000
```

Use this band when output must be governed, on-brand, and repeatable — the agent picks *which* visual, never *what HTML*.

## Band 2 — Declarative, A2UI with a custom catalog (`apps/declarative/web` + `apps/declarative/agent`)

[A2UI](https://docs.copilotkit.ai/a2a/generative-ui/declarative-a2ui) is an open, JSON-based specification (Google-led, with CopilotKit as a launch partner) where the agent emits **operations** instead of markup:

- `createSurface` — declares a surface bound to a component catalog.
- `updateComponents` — supplies a flat component tree (every component has an `id`; exactly one is `root`).
- `updateDataModel` — writes data the components bind to via `{ "path": "/report/title" }` pointers.

Three pieces make the band work (the course's Lego analogy): the **catalog** is the box of pieces, the **schema** is how they snap together, and the **data bindings** fill in the final details. This demo defines a custom catalog (`copilotkit://risk-catalog`) in `apps/declarative/web/src/catalog/` — definitions (Zod contracts the agent reads) plus renderers (React + Recharts implementations: `Metric` with trends, `BarChart`, `PieChart`, `DashboardCard`, `DataTable`, `Badge`…). Registering it on `CopilotKitProvider` via `a2ui={{ catalog: riskCatalog }}` also ships the component schemas to the agent as context.

Both A2UI schema styles coexist in the **same agent** (`apps/declarative/agent/main.py`), exactly like the course's L4:

- **Fixed schema** (`executive` / `brief`): a planner fabricates a `renderRiskReport` tool call (the LLM only picks layout + quarter, with a keyword fallback so this path works with no model at all), and a real LangGraph `ToolNode` executes it, returning pre-authored operations from `src/report_catalog.py` — chart/metric/table data baked inline, titles and the ranked list path-bound to the data model. Executing a *real* tool matters: `ag-ui-langgraph` only emits discrete `TOOL_CALL_*` events from `on_tool_end`, and the A2UI middleware only scans `TOOL_CALL_RESULT` events (messages replayed via `MESSAGES_SNAPSHOT` are **not** scanned).
- **Dynamic schema** (`freeform`): the runtime route enables `a2ui: { injectA2UITool: true }`; the agent binds the injected `render_a2ui` tool with `a2ui_prompt(schema)` and **streams** (`model.astream`, never `ainvoke` — progressive rendering rides on `on_chat_model_stream`), letting the LLM assemble the layout itself from the same catalog. The middleware parses the streamed arguments progressively, so the surface builds live in chat.

Run it:

```bash
cp apps/declarative/agent/.env.example apps/declarative/agent/.env   # set RISK_MODEL_ENDPOINT
npm run install:declarative-agent
npm run dev:declarative-agent   # :8124
npm run dev:declarative-web     # :3001
```

Contract tests in `apps/declarative/agent/tests/test_report_catalog.py` enforce the invariants that make the fixed path safe to demo live: unique ids, a single `root`, a DAG over known catalog components, non-empty inline chart/table data, and every data binding resolving against the generated data model.

Use this band when hand-authoring every layout doesn't scale but you still want a bounded vocabulary: fixed schemas for polished, high-traffic surfaces; dynamic schemas for the long tail. The [A2UI Composer](https://a2ui-editor.ag-ui.com/) is the visual editor for authoring fixed schemas.

## Band 3 — Open-Ended: MCP Apps + sandboxed UI (`apps/open-ended/web` + `apps/open-ended/agent`)

The far end of the spectrum (course L5): no registered components, no catalog. Two mechanisms, both enabled purely in the runtime route (`apps/open-ended/web/src/app/api/copilotkit/route.ts`):

```ts
openGenerativeUI: true,   // client registers a `generateSandboxedUi` frontend tool
mcpApps: { servers: [{ type: "http", url: "https://mcp.excalidraw.com", serverId: "excalidraw" }] },
```

- **`openGenerativeUI`**: when `/info` advertises it, the client registers a `generateSandboxedUi` tool. The agent generates arbitrary HTML/CSS/JS, streamed parameter-by-parameter (css → html → js); the middleware emits `open-generative-ui` activity deltas and the client renders the UI **as it is being written** inside a sandboxed iframe (no same-origin access; CDN libraries allowed).
- **MCP Apps**: the middleware discovers UI tools from the configured MCP servers and appends them to the agent's tool list. When the agent calls one (e.g. Excalidraw's `create_view`), the middleware executes it against the MCP server and emits an `mcp-apps` activity — a full application embedded in the chat. Same app protocol used by Claude and ChatGPT hosts.

The one-node graph in `apps/open-ended/agent/main.py` simply binds **all** injected tools to the Foundry model with a domain preamble and tool guidance, and streams. Run the same prompt twice and you get two different results — that nondeterminism *is* the demo, and the governance caveat.

Run it:

```bash
cp apps/open-ended/agent/.env.example apps/open-ended/agent/.env   # set RISK_MODEL_ENDPOINT (strong model recommended)
npm run install:open-ended-agent
npm run dev:open-ended-agent   # :8125
npm run dev:open-ended-web     # :3002
```

### Governance considerations for the open band

- **The tools' contracts are the only fence.** Generated UI runs in a sandboxed iframe and MCP apps are host-mediated, but layout, structure and quality vary run to run.
- **Prompt injection surface.** Anything that reaches the model (user text, retrieved data) can influence the generated UI. Never give the open band tools with side effects beyond rendering.
- **No pre-review.** Unlike the declarative band, there is nothing to review before runtime — a poor fit for regulated, executive-facing analytics, which is why the Genie demo stays in the controlled band.
- **External dependency.** MCP Apps need network access to the MCP server (`mcp.excalidraw.com` here) during the session.

## AG-UI vs A2UI in one paragraph

**AG-UI** is the transport: an event protocol (text messages, tool calls, state deltas, activities, custom events) between any agent runtime and any frontend — every demo here speaks it. **A2UI** is a payload format that travels *over* AG-UI: declarative UI operations (`createSurface` / `updateComponents` / `updateDataModel`) that a generic renderer turns into components. Controlled generative UI uses AG-UI tool calls bound to your own React components; declarative uses A2UI operations rendered against a catalog; open-ended skips both and ships sandboxed generated code or embedded MCP apps as activity messages.

## Version pinning

The A2UI middleware and renderer live on the CopilotKit v2 line. The repo pins exact versions for session reproducibility:

- npm: `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`, `@copilotkit/a2ui-renderer` at `1.55.2-next.1` (the `next` dist-tag moves; the pinned build is what the demos were verified against). Note the runtime `a2ui` option is an **object** in this build (`a2ui: {}`), not a boolean.
- pip: `copilotkit>=0.1.89,<0.2.0` — `0.1.89` is the first version verified to ship the `copilotkit.a2ui` helpers (`create_surface`, `update_components`, `update_data_model`, `render`, `a2ui_prompt`). There is no `begin_rendering` operation in this version; the renderer starts at the component with `id="root"`.
- pip: `ag-ui-langgraph>=0.0.41,<0.0.42` in the two new agents. Caveat that motivated the pin: the bridge maps the catalog-schema context entry to `state["ag-ui"]["a2ui_schema"]` by matching its exact description string, and that wording drifted between client and bridge versions ("props" vs "properties"). The declarative agent also scans the regular context as a version-tolerant fallback (`_a2ui_schema_from` in `main.py`).

When bumping any of these, re-run the demo beats in [docs/session-guide.es.md](session-guide.es.md) before presenting.
