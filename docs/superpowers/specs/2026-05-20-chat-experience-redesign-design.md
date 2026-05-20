# Chat Experience Redesign — Design

**Date:** 2026-05-20
**Status:** Approved (pending spec review)
**Area:** `apps/web` (frontend) + minimal `apps/agent` (backend) touch points

## Goal

Make the chat panel look modern, larger, and premium, and surface the agent's
process the way Anthropic/ChatGPT do: a streaming **Thinking** card, visible
**tool execution**, and smooth event transitions — leveraging CopilotKit v2 and
AG-UI properly instead of dumping raw progress text.

Secondary goal (first-class): leave the codebase **clean and refactored** —
remove legacy/dead code, and keep backend and frontend well-structured and
aligned around a single event contract.

## Context (current state)

- Frontend uses CopilotKit v2 (`@copilotkit/react-core/v2`, `next`) with a
  `CopilotChat` on the right and a separate `DashboardStage` on the left.
- Generative UI (charts/tables/KPIs) renders to the **left dashboard**, fed by
  render-bridge components (`DashboardPlanBridge`, `DashboardToolStatusBridge`
  via `useDefaultRenderTool`, `DashboardVisualBridge`).
- The backend (`apps/agent/main.py`) emits a rich **structured** AG-UI custom
  event, `risk_ui_event` (kinds: `reasoning.*`, `plan.created`, `approval.*`,
  `query.*`, `normalization.*`, `visualization.*`, `followups.suggested`,
  `error.safe`), **but the frontend never subscribes to it.**
- The backend also emits per-phase **text** via `manually_emit_message`, which
  surfaces as noisy standalone assistant bubbles, plus a one-shot
  `AgentStatusCard` component message.
- Net result: the "thinking" experience is fragmented (loose text bubbles + a
  static status card), and the chat is visually plain.

## Decisions (from brainstorming)

1. **Keep the split layout.** Dashboard (left) = results. Chat (right) =
   conversation + enriched process.
2. **Thinking = collapsible Claude/ChatGPT-style card.** Streams phases while
   running; collapses to "Thought for Xs · N steps" (expandable) when done.
3. **Rebalance + scale.** Give the chat column more width; increase typography,
   bubble, and spacing scale.
4. **Modernize while keeping the Foundry+Genie brand** (cream / purple / red).
5. **Drive the process from `risk_ui_event`** (Approach A): consume the
   structured stream that already exists; stop relying on raw progress bubbles.

## Architecture

### Event flow (target)

```
Backend (apps/agent)                     Frontend (apps/web)
─────────────────────                    ───────────────────
adispatch_custom_event(                  useAgent() event subscription
  "risk_ui_event", envelope)  ───────▶   → process-store (new, ligero)
                                              │
                                              ├─▶ ProcessTrace (chat, inline)
                                              └─▶ DashboardStage timeline (left)

render component messages (charts)  ──▶  useComponent renderers → DashboardStage
useRenderTool / toolCallsView       ──▶  inline tool chips (chat)
final AIMessage (answer only)       ──▶  assistantMessage bubble
```

The structured event becomes the **single source of truth** for process state.
Per-phase `manually_emit_message` text bubbles are removed so the chat shows
only: user messages, the live ProcessTrace, inline tool chips, generative UI
(routed to dashboard), the MCP approval card, the final answer, and follow-ups.

### New / changed units

| Unit | Responsibility | Depends on |
|------|----------------|------------|
| `process-store.ts` (new) | External store of ordered process steps + run status for the current run. Derived purely from `risk_ui_event`. | `contracts.ts` |
| `use-risk-ui-events.tsx` (new hook) | Subscribe to the agent's `risk_ui_event` custom events, validate with the Zod envelope, push into `process-store`. Single subscription point. | `useAgent`, `contracts.ts`, `process-store.ts` |
| `process-trace.tsx` (new) | Collapsible Thinking card. Live streaming of phase lines while running; collapses to summary on complete. Consumes `process-store`. | `process-store.ts` |
| `chat-message-views.tsx` (new) | `messageView` slot implementations: custom `assistantMessage`, `userMessage`, `cursor`, and inline `toolCallsView` chip rendering. | CopilotKit v2 slots |
| `tool-chip.tsx` (new) | Single tool-call chip: running shimmer → done check, with tool name + status. | — |
| `page.tsx` (changed) | Wire `messageView` slots + render `ProcessTrace`; mount `use-risk-ui-events`. | above |
| `globals.css` (changed) | Rebalanced grid, larger type scale, modern bubbles, ProcessTrace + chip styles, refined keyframes. | — |
| `dashboard-store.ts` (changed) | Timeline now fed from the shared process-store / event stream rather than ad-hoc bridge calls, so chat and dashboard show a consistent process. | `process-store.ts` |

### Where ProcessTrace lives in the message flow

`ProcessTrace` is rendered inline in the chat for the active run via the chat
view. While `agent.isRunning`, it shows the live streaming card. On completion
it persists as the collapsed "Thought for Xs · N steps" summary for that run.
(Single-run demo scope: one ProcessTrace per run, anchored to the run's
position in the conversation. Implementation detail — native `cursor` slot vs.
component message — is settled in the plan; both keep the summary visible after
completion.)

### Reasoning honesty

The "thinking" content is the **orchestrator's phase narrative** (route choice,
plan, approval, query, normalize, visualize), not the model's raw
chain-of-thought (Foundry does not stream reasoning tokens here). The UI mirrors
ChatGPT/Claude *form* over real, meaningful phases — no fabricated token stream.

## Visual / UX deliverables

1. **Layout & scale** — rebalance `split-grid` to widen the chat; raise base
   font size; refine `copilotTheme` tokens; more generous bubble padding and
   spacing.
2. **Modern bubbles** — `assistantMessage` (clean, brand-aligned) and
   `userMessage` (right-aligned, brand tint); larger type, clear hierarchy,
   entrance transition.
3. **ProcessTrace** — collapsible Thinking card: "Thinking…" header + animated
   indicator while running, staggered phase lines with per-step status dots;
   collapses to "Thought for Xs · N steps" (expandable).
4. **Inline tool chips** — `useRenderTool` / `toolCallsView` chips: running
   shimmer → done check.
5. **Streaming cursor** — branded animated `messageView.cursor`.
6. **Micro-animations** — staggered phase entrance, message transitions, refined
   existing keyframes (reuse where possible, prune unused).
7. **Consistency pass** — restyle `McpApprovalCard` and `FollowUpQuestions` to
   the new system.

## Cleanup / refactor (first-class requirement)

Identify and remove legacy/dead code; align backend and frontend on one
contract. Concrete targets to evaluate during implementation:

- **Backend:** stop emitting per-phase `manually_emit_message` text as separate
  chat bubbles (keep only the final answer as text); ensure every meaningful
  phase is covered by a `risk_ui_event`. Verify `apps/agent/src/ui_event_contract.py`
  and the frontend `contracts.ts` enumerate the **same** event kinds/phases
  (single shared contract semantics).
- **Frontend:** retire the static `AgentStatusCard` tones now superseded by
  `ProcessTrace` (remove the component, its `useComponent` registration, its
  Zod props, CSS, and any backend emission) **if** ProcessTrace fully replaces
  it; otherwise document why it stays. Remove now-unused store helpers (e.g.
  ad-hoc `setDashboardToolStatus` bridge calls) once the event stream feeds the
  timeline. Prune unused CSS keyframes/classes and dead exports.
- **General:** no orphaned imports, no unused Zod schemas, consistent naming
  between backend event kinds and frontend handlers.

A short "removed/kept" inventory will be produced during implementation so the
cleanup is auditable, not silent.

## Error handling

- `error.safe` events render a distinct error state in ProcessTrace (red dot)
  and the run collapses to "Stopped · N steps"; the final safe error AIMessage
  still renders as a normal assistant bubble.
- Event validation: malformed `risk_ui_event` payloads are dropped (Zod
  `safeParse`) and logged in dev, never crashing the chat.

## Testing

- **Backend:** extend `apps/agent/tests/test_ui_contracts.py` to assert the
  event-kind/phase enums stay in sync with what `main.py` emits, and that the
  final assistant text is the answer (no per-phase text bubbles).
- **Frontend:** unit-test `process-store` reducer (ordered steps, status
  transitions, duration) and the `risk_ui_event` → step mapping. Component-level
  smoke test that ProcessTrace renders running vs. collapsed states.
- **Manual:** run the frontend, exercise the four starter prompts + the HITL
  approval path, confirm streaming → collapse, tool chips, and the dashboard
  timeline stay consistent.

## Out of scope

- Bringing charts inline into the chat (charts stay in the dashboard).
- Real model chain-of-thought streaming (backend doesn't emit it).
- Multi-run conversation history redesign beyond per-run ProcessTrace.
- Backend orchestration logic changes beyond event/message hygiene.
