# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Categories used: **Added** (new functionality), **Changed** (behavior or contract changes), **Deprecated**, **Removed**, **Fixed**, **Security**.

## [Unreleased]

The repository now covers the full Generative UI spectrum with one runnable demo per band (Controlled / Declarative / Open-Ended), prepared for the "Build interactive Agents with Generative UI on Azure" session.

### Added

- Declarative band demo (`apps/declarative/web` + `apps/declarative/agent`, ports 3001/8124), mirroring the DeepLearning.AI course L4: a custom A2UI component catalog (`copilotkit://risk-catalog` — `Metric` with trends, Recharts `BarChart`/`PieChart`, `DashboardCard`, `DataTable`, `Badge`…) defined as Zod definitions + React renderers and registered via `CopilotKitProvider a2ui={{ catalog }}`. One agent serves both schema styles: **fixed** (planner fabricates a `renderRiskReport` tool call, a real `ToolNode` returns pre-authored operations; keyword fallback keeps it working with no model at all) and **dynamic** (`freeform` route binds the injected `render_a2ui` tool and streams, so the LLM-composed surface renders progressively). Contract tests validate the fixed trees (single `root`, DAG over the catalog, inline chart/table data, every binding resolvable).
- Open-ended band demo (`apps/open-ended/web` + `apps/open-ended/agent`, ports 3002/8125), mirroring the course L5: `openGenerativeUI: true` (the agent writes sandboxed HTML/CSS/JS via the client-registered `generateSandboxedUi` tool, rendered live while streaming) plus `mcpApps` with the public Excalidraw server (the runtime discovers the MCP tools, executes the call, and embeds the whiteboard in chat). The agent binds all injected tools and streams. Requires only `FOUNDRY_MODEL_ENDPOINT` — no Databricks (Excalidraw needs internet).
- Controlled-band frontend tools: `spotlightVisual` (highlight one visual, dim the rest) and `setPresentationMode` (hide the app chrome), driven through the existing `dashboard_op` route, replayed into the agent-readable dashboard context (`view` key), and rendered via new `useRenderTool` bridges backed by a `view-store`.
- Docs: `docs/generative-ui-spectrum.md` (band-by-band mechanics, AG-UI vs A2UI, governance trade-offs, version notes) and `docs/session-guide.es.md` (guion de sesión de 45–60 min con prompts por demo, tiempos y fallbacks), plus a grouped documentation index at `docs/README.md` and a README per band under `apps/`.
- Root scripts and npm workspaces for the new apps (`dev:*`, `install:*`, `validate:*` per demo); `scripts/validate-agent.sh` and `scripts/build-hosted-agent-image.sh` now take the agent directory as an argument.
- Foundry Hosted Agent scaffolding for the two new agents, mirroring the Genie agent: `hosted_main.py` (Invocations protocol), `Dockerfile`, `agent.yaml`, and `RISK_MODEL_*` env names (the `FOUNDRY_*` prefix is reserved inside hosted containers; the old names keep working as local fallbacks). The declarative and open-ended web routes support `AG_UI_AGENT_AUTH=azure-identity` for hosted endpoints.
- Deployment path for the whole spectrum (`docs/deploying-the-spectrum.md`): Bicep now provisions up to three frontends on one shared App Service plan (`deployControlledFrontend` / `deployDeclarativeFrontend` / `deployOpenEndedFrontend` + per-band agent URLs, replacing `deployFrontendApp`/`frontendAgUiAgentUrl`), grants every deployed frontend identity Foundry invoke access and the Foundry project identity `Cognitive Services OpenAI User` (hosted agents calling the model), and the spectrum nav buttons resolve from build-time `NEXT_PUBLIC_SPECTRUM_URL_*` env vars (localhost fallback).
- OpenTelemetry tracing for the three hosted agents: a per-band `src/observability.py` builds `langchain-azure-ai`'s native `AzureAIOpenTelemetryTracer` and wires it into each `build_ag_ui_agent()` via `config={"callbacks": …}`, so GenAI chat/tool spans (tokens, cost, evaluators) land in Foundry Observability instead of a bare `invoke_agent` span. The tracer auto-detects the App Insights connection string (`APPLICATIONINSIGHTS_CONNECTION_STRING`, injected in-container) or the project endpoint and degrades to a no-op locally; the controlled band additionally traces its delegated genie call (`get_agent_node(trace=True)`). Adds the `[opentelemetry]` extra to the declarative and open-ended agents (controlled already had it).

### Changed

- `npm run validate` and CI now cover all three agents (ruff/mypy/pytest/py_compile) and all three frontends (lint/test/build); the pip cache key includes the three pyprojects.
- CopilotKit packages pinned for session reproducibility: npm `@copilotkit/*` at `1.55.2-next.1` (was floating `next`), Python `copilotkit>=0.1.89,<0.2.0` (first version shipping the `a2ui` helpers), and `ag-ui-langgraph>=0.0.41,<0.0.42` in the new agents — plus a version-tolerant fallback in the declarative agent because the catalog-schema context description drifted between client and bridge versions ("props" vs "properties").

### Fixed

- Controlled agent crashed at import inside the hosted-agent container (`session_not_ready`): the repo-root lookup used a fixed `parents[N]` that does not exist in the container's flat `/app/user_agent` layout. `config.py` now walks up looking for `.foundry/` and degrades cleanly where it is absent.
- Open-ended sandboxed widgets sometimes rendered with placeholder values ("—", 0.0%) when the model deferred data population to JS init that never ran: the agent guidance now requires real data inline in the HTML and `jsExpressions`-driven initialization (no load events).
- Multi-turn conversations in the open-ended and declarative-dynamic demos no longer fail with "No tool output found for function call": both agents repair orphan tool calls in the history (the open-generative-ui middleware renders the streamed call client-side but never synthesizes a tool result) before invoking the model.
- README reframed around the three-band spectrum with a demo matrix, per-band run commands, and a "where do I start" docs hub.
- `apps/` restructured into band folders — `apps/controlled/{web,agent}`, `apps/declarative/{web,agent}`, `apps/open-ended/{web,agent}` — with npm scripts renamed to match (`dev:controlled-web`, `validate:open-ended-agent`, …). The new agents follow a thin-entrypoint layout: `main.py` (local bridge) / `hosted_main.py` (Foundry) with all logic under `src/` (`graph.py`, `planner.py`, `history.py`, `llm.py`, `config.py`); the duplication between the declarative and open-ended agents is deliberate so each band stays a standalone, copyable teaching unit.
- Declarative freeform (dynamic-schema) A2UI surfaces rendered "A2UI render error: Catalog not found: …/v0_9/basic_catalog.json" because the model never emitted a `catalogId`, so `@ag-ui/a2ui-middleware` materialized the surface against the v0.9 *basic* catalog the frontend never registers (`includeBasicCatalog: false`). The dynamic agent now resolves the catalog id (`_catalog_id_from` — the id shipped in the client schema, else the app's `copilotkit://risk-catalog` constant) and pins it in the render prompt so every `render_a2ui` call binds to the custom catalog (the fixed schema already stamped it via `a2ui.create_surface`). Verified live against gpt-5-4.

### Removed

- Dead code from the controlled web app: the unused `@copilotkit/react-ui`, Tailwind and `@eslint/eslintrc` dependencies (never wired) and the orphaned `approval-*` CSS left behind when HITL was removed in 0.1.0.

## [0.1.0] - 2026-05-23

Initial public release. Demo of Generative UI on Microsoft Foundry hosted agents and Databricks Genie, served through a CopilotKit + AG-UI Next.js frontend.

### Added

- End-to-end Risk & Exposure demo wired through Microsoft Foundry hosted agents, Databricks Genie, and a CopilotKit / AG-UI Next.js frontend.
- LangGraph supervisor that routes user turns between greeting, direct answer, and dashboard-op nodes, with a direct-route fallback when the supervisor call fails.
- Foundry hosted AG-UI agent support, including `scripts/setup-foundry-genie-agent.sh` and `.foundry/agent-metadata.example.yaml`.
- Application Insights tracing wired through `langchain-azure-ai[opentelemetry]` so every Foundry call surfaces in the same trace.
- Optional frontend deployment to Azure App Service via Bicep modules under `infra/modules/`.
- Dashboard architecture in `apps/web`:
  - Client-side `DatasetStore` and `DashboardStore` with add / remove / retype / reorder / clear semantics.
  - Pure `dataset-derive` aggregation builder rendering visuals from cached datasets.
  - Chat-driven dashboard edits through a `dashboard_op` route on the agent and frontend tools hooked via render-tool side-effects.
- Process-store derived from `risk_ui_event`, feeding a collapsible `ProcessTrace` thinking card and a planning skeleton.
- Synthetic risk dataset covering 8 quarters and roughly 112 policies for offline demos.
- Executive summary card with collapsible reasoning disclosure.
- Vitest setup for pure-logic unit tests in `apps/web`, plus `pytest` + `pytest-asyncio` in `apps/agent`.
- Open-source scaffolding for going public:
  - `LICENSE` (MIT).
  - `SECURITY.md` with private vulnerability reporting policy.
  - `CODE_OF_CONDUCT.md` adopting Contributor Covenant 2.1.
  - `.github/ISSUE_TEMPLATE/` (bug, feature, config routing to upstream platforms), `PULL_REQUEST_TEMPLATE.md`, and `CODEOWNERS`.
- CI improvements (`.github/workflows/ci.yml`):
  - `pip` cache keyed on `apps/agent/pyproject.toml`.
  - New `bicep` job running `az bicep build infra/main.bicep` so IaC typos fail fast.
  - New `markdown-lint` job (informational while existing docs stabilize).
- New `link-check` workflow using `lychee`, scheduled weekly and triggerable manually — kept off the PR critical path so external link flakiness does not gate merges.
- `.github/dependabot.yml` watching GitHub Actions, npm (with grouped updates for `next`, `@copilotkit/*`, `@ag-ui/*`, and `@types/*`), and pip in `apps/agent`.
- README badges for CI status, license, changelog format, ruff, Next.js, and Python.
- `.editorconfig`, `.nvmrc`, and `.python-version` so editors and version managers pick the same runtimes as CI.

### Changed

- Chat surface docked as `CopilotSidebar` instead of a bespoke chat column; CopilotKit style clashes resolved.
- Dashboard timeline driven from the process-store; legacy duplicated state in the agent status card removed.
- Multi-card dashboard grid layout polished, with the `ProcessTrace` and cursor slot remounted and the type scale rebalanced.
- Governed provenance re-wired through the dataset-derive path so warnings travel with the dataset rather than the visual.
- Greetings routed through the LLM supervisor; the previous heuristic shortcut was removed.
- `apps/agent` emits structured `risk_ui_event` payloads only; the legacy status card stream was retired.

### Removed

- All human-in-the-loop and approval processes (agent gates, web approval cards, test-only approval helpers, and supervisory `pending_data_approvals` plumbing).
- `setup-foundry-genie-agent.sh` no longer creates the agent with `require_approval=always`; it now sets `require_approval=never` to match the runtime.
- Superseded direct-emit visualization path now that visuals derive from cached datasets.
- Legacy `AgentStatusCard`, dead `VisualMeta`, orphaned `ProcessTrace` store, and the associated CSS were pruned after the chat redesign.
- Internal `docs/superpowers/` workflow specs are no longer tracked.

### Fixed

- Foundry calls retry with exponential backoff on transient `429`s.
- Provenance footer guards against missing warnings instead of throwing.
- Suggested follow-up questions are re-emitted so the suggested-followups step renders consistently.
- Rows table renders even when no categorical dimension is available.
- Dashboard bridges validate tool-call arguments before mutating the store.
- Planning skeleton shows from `plan.created` through the wait phase.
- `azure-ai-agentserver-core` pinned to `2.0.0b3` to match `invocations==1.0.0b3` and unblock installs.
- Agent codebase passes `ruff format` and strict `mypy` so `npm run validate:agent` is green in CI.

### Security

- `.claude/` added to `.gitignore` so local agent permissions and tool allowlists are not pushed by accident.
- Pre-commit hooks include `detect-private-key`; `.env*`, `.risk.env.local`, `.foundry/agent-metadata.yaml`, and `.azure/` are gitignored by default.
- `SECURITY.md` documents the private vulnerability reporting flow and out-of-scope platforms (MSRC, Databricks).

[Unreleased]: https://github.com/alexandergg/foundry-genie-generative-ui/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alexandergg/foundry-genie-generative-ui/releases/tag/v0.1.0
