# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Categories used: **Added** (new functionality), **Changed** (behavior or contract changes), **Deprecated**, **Removed**, **Fixed**, **Security**.

## [Unreleased]

_Nothing yet._

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
