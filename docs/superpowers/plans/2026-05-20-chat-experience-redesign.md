# Chat Experience Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the CopilotKit v2 chat with a streaming Claude/ChatGPT-style "Thinking" card, inline tool chips, refined bubbles and layout — driven by the existing `risk_ui_event` stream — while removing legacy/dead code so backend and frontend share one event contract.

**Architecture:** A new frontend `process-store` (external store) is fed exclusively by the backend's structured `risk_ui_event` AG-UI custom events (subscribed via `agent.subscribe`). It powers a collapsible `ProcessTrace` in the chat and the dashboard timeline on the left. Tool execution renders as inline chips through `useDefaultRenderTool`. Per-phase text bubbles and the one-shot `AgentStatusCard` are removed; the chat shows user messages, the ProcessTrace, tool chips, generative UI (routed to the dashboard), the approval card, the final answer, and follow-ups.

**Tech Stack:** Next.js 16, React 19, CopilotKit v2 (`@copilotkit/react-core/v2`), `@ag-ui/client`, Zod, Recharts (existing), Vitest (new, for pure-logic tests); Python 3.10 + pytest (backend).

---

## File Structure

**New (frontend, `apps/web/src/components/generative-ui/`):**
- `process-store.ts` — external store of ordered process steps + run status, derived purely from `risk_ui_event`.
- `process-trace.tsx` — collapsible Thinking card (live streaming → "Thought for Xs · N steps").
- `tool-chip.tsx` — single inline tool-call chip (running shimmer → done check).

**New (frontend, `apps/web/src/hooks/`):**
- `use-risk-ui-events.tsx` — single subscription point: `risk_ui_event` + run lifecycle → `process-store`.

**New (frontend tooling):**
- `apps/web/vitest.config.ts` — Vitest config (node env).
- `apps/web/src/components/generative-ui/process-store.test.ts` — reducer unit tests.

**Modified (frontend):**
- `src/app/page.tsx` — mount the event hook, render `<ProcessTrace />`, wire `messageView` slots.
- `src/app/globals.css` — layout rebalance, type scale, ProcessTrace + ToolChip + bubble styles, prune dead CSS.
- `src/hooks/use-risk-generative-ui.tsx` — `useDefaultRenderTool` renders inline `ToolChip`; drop `agentStatusCard` registration.
- `src/components/generative-ui/dashboard-stage.tsx` — timeline reads from `process-store`; drop `DashboardToolStatusBridge`.
- `src/components/generative-ui/dashboard-store.ts` — remove timeline duplication (visuals + plan only).
- `src/components/generative-ui/types.ts` — remove `AgentStatusCardProps`.
- `src/components/generative-ui/registry.ts` — remove `agentStatusCard`.
- `apps/web/package.json` — add Vitest devDep + `test` script.

**Deleted (frontend):**
- `src/components/generative-ui/agent-status-card.tsx`.

**Modified (backend, `apps/agent/`):**
- `main.py` — `_emit_ui_event` stops emitting phase text bubbles; remove `_emit_progress`, `_agent_status_message`, `AGENT_STATUS_CARD`, and the status-card emission in `_execute_risk_query`.
- `src/component_registry.py` — remove `"agentStatusCard"`.
- `tests/test_ui_contracts.py` — assert contract sync + no phase-text emission.

---

## Task 1: Frontend test tooling (Vitest)

**Files:**
- Modify: `apps/web/package.json`
- Create: `apps/web/vitest.config.ts`

- [ ] **Step 1: Install dependencies**

The repo has no `node_modules` yet. Install, then add Vitest.

Run:
```bash
cd apps/web && npm install
npm install -D vitest@^2
```
Expected: installs complete without error; `vitest` appears under `devDependencies`.

- [ ] **Step 2: Add the test script**

In `apps/web/package.json`, add `"test"` to `scripts`:

```json
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "test": "vitest run"
  },
```

- [ ] **Step 3: Create the Vitest config (node env — pure logic only)**

Create `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

- [ ] **Step 4: Verify the runner works (no tests yet is OK)**

Run: `cd apps/web && npm run test`
Expected: Vitest runs and reports "No test files found" (exit 0) — confirms tooling is wired.

- [ ] **Step 5: Commit**

```bash
git add apps/web/package.json apps/web/package-lock.json apps/web/vitest.config.ts
git commit -m "chore(web): add Vitest for pure-logic unit tests"
```

---

## Task 2: process-store (TDD — pure logic)

The single source of truth for process/timeline state, derived from `risk_ui_event`. Mirrors the existing external-store pattern in `dashboard-store.ts` (subscribe / getSnapshot / emit).

**Files:**
- Create: `apps/web/src/components/generative-ui/process-store.ts`
- Test: `apps/web/src/components/generative-ui/process-store.test.ts`

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/generative-ui/process-store.test.ts`:

```ts
import { describe, it, expect, beforeEach } from "vitest";
import {
  startRun,
  applyUiEvent,
  finishRun,
  failRun,
  getProcessSnapshot,
  resetProcessStore,
} from "./process-store";
import { UI_EVENT_SCHEMA_VERSION } from "./contracts";

function envelope(kind: string, phase: string, message?: string) {
  return {
    schemaVersion: UI_EVENT_SCHEMA_VERSION,
    eventId: `${kind}-${Math.random()}`,
    kind,
    phase,
    timestamp: new Date().toISOString(),
    payload: message ? { message } : {},
  };
}

describe("process-store", () => {
  beforeEach(() => resetProcessStore());

  it("starts a run in the running state with no steps", () => {
    startRun();
    const s = getProcessSnapshot();
    expect(s.status).toBe("running");
    expect(s.steps).toHaveLength(0);
    expect(s.startedAt).toBeTypeOf("number");
  });

  it("appends a step from a valid event with detail from payload.message", () => {
    startRun();
    applyUiEvent(envelope("reasoning.started", "supervise", "Thinking…"));
    const [step] = getProcessSnapshot().steps;
    expect(step.kind).toBe("reasoning.started");
    expect(step.label).toBe("Reasoning");
    expect(step.detail).toBe("Thinking…");
    expect(step.status).toBe("active");
  });

  it("completes prior active steps when a new event arrives", () => {
    startRun();
    applyUiEvent(envelope("reasoning.started", "supervise"));
    applyUiEvent(envelope("query.started", "query"));
    const { steps } = getProcessSnapshot();
    expect(steps[0].status).toBe("complete");
    expect(steps[1].status).toBe("active");
  });

  it("marks the run errored on error.safe", () => {
    startRun();
    applyUiEvent(envelope("error.safe", "error", "Failed safely"));
    const s = getProcessSnapshot();
    expect(s.status).toBe("error");
    expect(s.steps[0].status).toBe("error");
  });

  it("drops malformed events without throwing", () => {
    startRun();
    applyUiEvent({ not: "an envelope" });
    expect(getProcessSnapshot().steps).toHaveLength(0);
  });

  it("finishRun completes active steps and records duration", () => {
    startRun();
    applyUiEvent(envelope("reasoning.started", "supervise"));
    finishRun();
    const s = getProcessSnapshot();
    expect(s.status).toBe("complete");
    expect(s.steps.every((step) => step.status === "complete")).toBe(true);
    expect(s.finishedAt).toBeTypeOf("number");
  });

  it("failRun sets error status", () => {
    startRun();
    failRun();
    expect(getProcessSnapshot().status).toBe("error");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npm run test`
Expected: FAIL — cannot resolve `./process-store` (module does not exist yet).

- [ ] **Step 3: Implement process-store**

Create `apps/web/src/components/generative-ui/process-store.ts`:

```ts
import { UiEventEnvelopeV1, type UiEventKind, type UiEventPhase } from "./contracts";

export type ProcessStepStatus = "active" | "complete" | "error";
export type ProcessRunStatus = "idle" | "running" | "complete" | "error";

export type ProcessStep = {
  id: string;
  kind: UiEventKind;
  phase: UiEventPhase;
  label: string;
  detail?: string;
  status: ProcessStepStatus;
  at: number;
};

export type ProcessState = {
  status: ProcessRunStatus;
  steps: ProcessStep[];
  startedAt?: number;
  finishedAt?: number;
};

const KIND_LABEL: Record<UiEventKind, string> = {
  "reasoning.started": "Reasoning",
  "reasoning.completed": "Reasoning",
  "plan.created": "Planning the analysis",
  "approval.requested": "Awaiting approval",
  "approval.updated": "Approval updated",
  "query.started": "Querying governed data",
  "query.completed": "Query complete",
  "normalization.started": "Normalizing results",
  "normalization.completed": "Normalization complete",
  "visualization.proposed": "Preparing visuals",
  "visualization.rendered": "Visuals rendered",
  "provenance.attached": "Provenance attached",
  "followups.suggested": "Suggested follow-ups",
  "error.safe": "Stopped safely",
};

const TERMINAL_KINDS = new Set<UiEventKind>([
  "reasoning.completed",
  "query.completed",
  "normalization.completed",
  "visualization.rendered",
  "approval.updated",
  "provenance.attached",
  "followups.suggested",
]);

let state: ProcessState = { status: "idle", steps: [] };
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function completeActive(steps: ProcessStep[]): ProcessStep[] {
  return steps.map((step) => (step.status === "active" ? { ...step, status: "complete" } : step));
}

export function subscribeProcess(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getProcessSnapshot(): ProcessState {
  return state;
}

export function resetProcessStore() {
  state = { status: "idle", steps: [] };
  emit();
}

export function startRun() {
  state = { status: "running", steps: [], startedAt: Date.now() };
  emit();
}

export function applyUiEvent(raw: unknown) {
  const parsed = UiEventEnvelopeV1.safeParse(raw);
  if (!parsed.success) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[process-store] dropped malformed risk_ui_event", parsed.error.issues);
    }
    return;
  }
  const envelope = parsed.data;
  const payload = (envelope.payload ?? {}) as { message?: string };
  const isError = envelope.kind === "error.safe";
  const step: ProcessStep = {
    id: envelope.eventId,
    kind: envelope.kind,
    phase: envelope.phase,
    label: KIND_LABEL[envelope.kind],
    detail: payload.message,
    status: isError ? "error" : TERMINAL_KINDS.has(envelope.kind) ? "complete" : "active",
    at: Date.now(),
  };
  state = {
    ...state,
    status: isError ? "error" : state.status,
    steps: [...completeActive(state.steps), step],
  };
  emit();
}

export function finishRun() {
  if (state.status === "error") {
    state = { ...state, finishedAt: state.finishedAt ?? Date.now() };
    emit();
    return;
  }
  state = {
    ...state,
    status: "complete",
    steps: completeActive(state.steps),
    finishedAt: Date.now(),
  };
  emit();
}

export function failRun() {
  state = { ...state, status: "error", finishedAt: Date.now() };
  emit();
}

export function getRunDurationSeconds(): number | undefined {
  if (state.startedAt == null || state.finishedAt == null) return undefined;
  return Math.max(0, Math.round((state.finishedAt - state.startedAt) / 1000));
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npm run test`
Expected: PASS — all 7 `process-store` tests green.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/generative-ui/process-store.ts apps/web/src/components/generative-ui/process-store.test.ts
git commit -m "feat(web): add process-store derived from risk_ui_event"
```

---

## Task 3: use-risk-ui-events hook

Single subscription point bridging `agent.subscribe` → `process-store`.

**Files:**
- Create: `apps/web/src/hooks/use-risk-ui-events.tsx`

- [ ] **Step 1: Implement the hook**

Create `apps/web/src/hooks/use-risk-ui-events.tsx`:

```tsx
"use client";

import { useEffect } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import type { AgentSubscriber } from "@ag-ui/client";
import { applyUiEvent, failRun, finishRun, startRun } from "@/components/generative-ui/process-store";

const RISK_UI_EVENT = "risk_ui_event";

export function useRiskUiEvents() {
  const { agent } = useAgent();

  useEffect(() => {
    const subscriber: AgentSubscriber = {
      onRunStartedEvent: () => startRun(),
      onCustomEvent: ({ event }) => {
        if (event.name === RISK_UI_EVENT) applyUiEvent(event.value);
      },
      onRunFinalized: () => finishRun(),
      onRunFailed: () => failRun(),
    };
    const { unsubscribe } = agent.subscribe(subscriber);
    return () => unsubscribe();
  }, [agent]);
}
```

- [ ] **Step 2: Type-check**

Run: `cd apps/web && npx tsc --noEmit`
Expected: PASS (no type errors in the new hook). If `AgentSubscriber` callback names differ in the installed `@ag-ui/client@0.0.52`, open `node_modules/@ag-ui/client/dist/index.d.ts`, find the `AgentSubscriber` interface, and use the exact callback names for run-started / run-finalized / run-failed / custom-event (the four lifecycle hooks); keep behavior identical.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/hooks/use-risk-ui-events.tsx
git commit -m "feat(web): subscribe risk_ui_event stream into process-store"
```

---

## Task 4: ProcessTrace (collapsible Thinking card)

**Files:**
- Create: `apps/web/src/components/generative-ui/process-trace.tsx`

- [ ] **Step 1: Implement the component**

Create `apps/web/src/components/generative-ui/process-trace.tsx`:

```tsx
"use client";

import { useSyncExternalStore, useState, useEffect } from "react";
import {
  subscribeProcess,
  getProcessSnapshot,
  getRunDurationSeconds,
  type ProcessStep,
} from "./process-store";

function StepRow({ step }: { step: ProcessStep }) {
  return (
    <li className={`process-step ${step.status}`}>
      <span className="process-step-dot" aria-hidden="true" />
      <div>
        <p>{step.label}</p>
        {step.detail ? <span>{step.detail}</span> : null}
      </div>
    </li>
  );
}

export function ProcessTrace() {
  const state = useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot);
  const [open, setOpen] = useState(true);
  const isRunning = state.status === "running";

  // Auto-expand while running; auto-collapse shortly after completion.
  useEffect(() => {
    if (isRunning) {
      setOpen(true);
      return;
    }
    if (state.status === "complete" || state.status === "error") {
      const timer = setTimeout(() => setOpen(false), 900);
      return () => clearTimeout(timer);
    }
  }, [isRunning, state.status]);

  if (state.status === "idle" || state.steps.length === 0) return null;

  const duration = getRunDurationSeconds();
  const summary = isRunning
    ? "Thinking…"
    : state.status === "error"
      ? `Stopped · ${state.steps.length} steps`
      : `Thought${duration != null ? ` for ${duration}s` : ""} · ${state.steps.length} steps`;

  return (
    <section className={`process-trace ${state.status}`} aria-label="Agent process">
      <button
        type="button"
        className="process-trace-header"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className={`process-trace-indicator ${isRunning ? "live" : ""}`} aria-hidden="true" />
        <strong>{summary}</strong>
        <span className="process-trace-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <ol className="process-trace-steps">
          {state.steps.map((step) => (
            <StepRow key={step.id} step={step} />
          ))}
        </ol>
      ) : null}
    </section>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `cd apps/web && npx tsc --noEmit`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/generative-ui/process-trace.tsx
git commit -m "feat(web): add collapsible ProcessTrace thinking card"
```

---

## Task 5: ToolChip + inline tool rendering

Replace the dashboard-routed default tool renderer with inline chips in the chat.

**Files:**
- Create: `apps/web/src/components/generative-ui/tool-chip.tsx`
- Modify: `apps/web/src/hooks/use-risk-generative-ui.tsx`

- [ ] **Step 1: Implement ToolChip**

Create `apps/web/src/components/generative-ui/tool-chip.tsx`:

```tsx
const PRETTY_NAME: Record<string, string> = {
  ask_genie: "Databricks Genie",
  query_genie: "Databricks Genie",
};

function prettify(name: string) {
  return PRETTY_NAME[name] ?? name.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ToolChip({ name, status }: { name: string; status: string }) {
  const done = status.toLowerCase() === "complete";
  return (
    <span className={`tool-chip ${done ? "done" : "running"}`}>
      <span className="tool-chip-icon" aria-hidden="true" />
      <span className="tool-chip-name">{prettify(name)}</span>
      <span className="tool-chip-status">{done ? "done" : "running"}</span>
    </span>
  );
}
```

- [ ] **Step 2: Render ToolChip inline; drop agentStatusCard registration**

In `apps/web/src/hooks/use-risk-generative-ui.tsx`:

Remove the `agentStatusCard` registration line (the `useComponent` whose name is `GENERATIVE_UI_COMPONENTS.agentStatusCard`) and remove `AgentStatusCard`, `AgentStatusCardProps`, and the now-unused `DashboardToolStatusBridge` from the imports.

Replace the `useDefaultRenderTool` block at the bottom:

```tsx
  useDefaultRenderTool({
    render: ({ name, status }) => <ToolChip name={name} status={status} />,
  });
```

Add the import near the other component imports:

```tsx
import { ToolChip } from "@/components/generative-ui/tool-chip";
```

And update the `dashboard-stage` import to drop `DashboardToolStatusBridge`:

```tsx
import { DashboardPlanBridge, DashboardVisualBridge } from "@/components/generative-ui/dashboard-stage";
```

- [ ] **Step 3: Type-check**

Run: `cd apps/web && npx tsc --noEmit`
Expected: errors only where `DashboardToolStatusBridge` / `AgentStatusCard` are still referenced elsewhere (resolved in Tasks 6 & 8). The hook file itself must be clean.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/generative-ui/tool-chip.tsx apps/web/src/hooks/use-risk-generative-ui.tsx
git commit -m "feat(web): render tool calls as inline chips, drop dashboard tool bridge"
```

---

## Task 6: Dashboard timeline reads from process-store

Make `process-store` the single timeline source; `dashboard-store` keeps only visuals + plan.

**Files:**
- Modify: `apps/web/src/components/generative-ui/dashboard-store.ts`
- Modify: `apps/web/src/components/generative-ui/dashboard-stage.tsx`

- [ ] **Step 1: Trim dashboard-store to visuals + plan**

In `apps/web/src/components/generative-ui/dashboard-store.ts`:
- Remove `DashboardTimelineEvent`, `TimelineEventStatus`, the `timeline` field from `DashboardState`, `completePreviousEvents`, `appendTimelineEvent`, and the exported `setDashboardToolStatus`.
- Keep `phase`, `plan`, `visuals` and the functions `setDashboardPlanning`, `publishDashboardVisual`, `subscribeDashboard`, `getDashboardSnapshot`.

Resulting state shape:

```ts
export type DashboardState = {
  phase: DashboardPhase;
  plan?: VisualizationPlanProps;
  visuals: DashboardVisual[];
};

let dashboardState: DashboardState = { phase: "idle", visuals: [] };
```

`setDashboardPlanning` becomes:

```ts
export function setDashboardPlanning(plan?: VisualizationPlanProps) {
  dashboardState = { phase: "planning", plan, visuals: [] };
  emit();
}
```

`publishDashboardVisual` drops the `appendTimelineEvent(...)` call but keeps the visuals update:

```ts
export function publishDashboardVisual(visual: DashboardVisual) {
  const withoutCurrent = dashboardState.visuals.filter((item) => item.id !== visual.id);
  dashboardState = {
    ...dashboardState,
    phase: "ready",
    visuals: [...withoutCurrent, visual].sort(
      (a, b) => DASHBOARD_VISUAL_PRIORITY[a.type] - DASHBOARD_VISUAL_PRIORITY[b.type],
    ),
  };
  emit();
}
```

- [ ] **Step 2: Point the dashboard timeline at process-store**

In `apps/web/src/components/generative-ui/dashboard-stage.tsx`:
- Remove the `DashboardToolStatusBridge` export and `setDashboardToolStatus` import.
- Render the existing `status-timeline` UI from `process-store` steps instead of `state.timeline`. Read it with a second `useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot)` and map `ProcessStep` → the existing `.timeline-step` markup (`step.status` already matches the `active | complete | error` classes; use `step.label` and `step.detail`).

Concretely, add the import:

```tsx
import { getProcessSnapshot, subscribeProcess } from "./process-store";
```

and inside the component that renders the timeline:

```tsx
const process = useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot);
// ...render process.steps with the existing .status-timeline / .timeline-step markup,
// using step.status for the class, step.label for the title, step.detail for the subtext.
```

- [ ] **Step 3: Type-check**

Run: `cd apps/web && npx tsc --noEmit`
Expected: errors only from remaining `AgentStatusCard`/`agentStatusCard` references (Task 8). No errors referencing `timeline`, `setDashboardToolStatus`, or `DashboardToolStatusBridge`.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/generative-ui/dashboard-store.ts apps/web/src/components/generative-ui/dashboard-stage.tsx
git commit -m "refactor(web): drive dashboard timeline from process-store, drop store duplication"
```

---

## Task 7: Wire page.tsx + cursor slot + layout/type scale

**Files:**
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Mount the event hook and render ProcessTrace; add the cursor slot**

In `apps/web/src/app/page.tsx`:

Add imports:

```tsx
import { useRiskUiEvents } from "@/hooks/use-risk-ui-events";
import { ProcessTrace } from "@/components/generative-ui/process-trace";
```

Call the hook alongside the existing one at the top of `HomePage`:

```tsx
  useRiskGenerativeUI();
  useRiskUiEvents();
```

Restructure `.chat-wrap` so ProcessTrace sits above the chat as a flex column. Replace the `chat-wrap` block so it renders `<ProcessTrace />` between the placeholder and `<CopilotChat>`:

```tsx
          <div className="chat-wrap" ref={chatWrapRef}>
            {!hasStartedChat && (
              <div className="chat-placeholder">
                <div className="chat-intro-logo">
                  <DatabricksGenieMark animated />
                </div>
                <p>Start with a governed risk question.</p>
                <div className="chat-intro-pulses" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <ProcessTrace />
            <CopilotChat
              labels={{
                welcomeMessageText: " ",
                chatInputPlaceholder: "Ask about exposure, claims, brokers, or overdue risk…",
                chatDisclaimerText: " ",
              }}
              chatView="risk-copilot-chat-view"
              messageView={{
                cursor: () => <span className="chat-cursor" aria-label="Assistant is responding" />,
              }}
            />
          </div>
```

- [ ] **Step 2: Layout rebalance + type scale + new component styles**

In `apps/web/src/app/globals.css`:

(a) **Rebalance the split grid** — locate the `.split-grid` (or `.main-grid.split-grid`) rule and give the chat more width. If it currently uses `grid-template-columns` favoring the dashboard, change the chat column to a larger minimum, e.g.:

```css
.main-grid.split-grid { grid-template-columns: minmax(0, 1.45fr) minmax(420px, 0.95fr); }
```

(b) **Make `.chat-wrap` a flex column** so ProcessTrace stacks above the chat:

```css
.chat-wrap { display: flex; flex-direction: column; }
.chat-wrap .copilotKitChat,
.chat-wrap .risk-copilot-chat-view { flex: 1; min-height: 0; }
```

(c) **Scale up chat typography/bubbles** — update the assistant bubble rule and input to larger, more generous sizing:

```css
.chat-wrap .copilotKitAssistantMessage > .cpk\:prose {
  max-width: min(88%, 46rem);
  padding: 13px 16px;
  font-size: 15px;
  line-height: 1.55;
  border-radius: 20px 20px 20px 8px;
}
.chat-wrap .copilotKitUserMessage > * {
  font-size: 15px;
}
.chat-wrap .copilotKitInput { font-size: 15px; }
```

(d) **ProcessTrace styles** (brand-aligned, modern):

```css
.process-trace { margin: 10px 14px; border: 1px solid rgba(91,70,255,.16); border-radius: 16px; background: linear-gradient(135deg, rgba(91,70,255,.06), rgba(255,255,255,.9)); box-shadow: 0 10px 28px rgba(20,20,19,.05); overflow: hidden; animation: fadeUp .3s ease both; }
.process-trace.error { border-color: rgba(200,70,70,.22); background: linear-gradient(135deg, rgba(200,70,70,.06), rgba(255,255,255,.9)); }
.process-trace-header { display: flex; align-items: center; gap: 9px; width: 100%; padding: 11px 14px; border: 0; background: transparent; cursor: pointer; color: #2f2d28; font: inherit; text-align: left; }
.process-trace-header strong { flex: 1; font-size: 13.5px; letter-spacing: -.01em; }
.process-trace-chevron { color: var(--muted); font-size: 12px; }
.process-trace-indicator { width: 9px; height: 9px; border-radius: 999px; background: var(--green, #19a974); box-shadow: 0 0 0 5px rgba(25,169,116,.12); }
.process-trace-indicator.live { background: #5b46ff; box-shadow: 0 0 0 5px rgba(91,70,255,.12); animation: typingPulse 1.4s ease-in-out infinite; }
.process-trace-steps { display: grid; gap: 4px; margin: 0; padding: 0 14px 12px 14px; list-style: none; }
.process-step { display: grid; grid-template-columns: 12px minmax(0,1fr); gap: 10px; align-items: start; padding: 5px 0; animation: fadeUp .26s ease both; }
.process-step-dot { width: 8px; height: 8px; margin-top: 6px; border-radius: 999px; background: rgba(91,70,255,.5); }
.process-step.complete .process-step-dot { background: var(--green, #19a974); }
.process-step.error .process-step-dot { background: var(--red, #c84646); }
.process-step.active .process-step-dot { background: #5b46ff; box-shadow: 0 0 0 4px rgba(91,70,255,.12); animation: typingPulse 1.3s ease-in-out infinite; }
.process-step p { margin: 0; font-size: 13px; font-weight: 640; color: #302e29; }
.process-step span { display: block; margin-top: 2px; color: var(--muted); font-size: 12px; line-height: 1.4; }
```

(e) **ToolChip styles**:

```css
.tool-chip { display: inline-flex; align-items: center; gap: 7px; margin: 6px 0; padding: 6px 11px; border: 1px solid rgba(31,30,26,.1); border-radius: 999px; background: rgba(255,255,255,.86); font-size: 12px; font-weight: 600; color: #3a3833; box-shadow: 0 6px 16px rgba(20,20,19,.04); }
.tool-chip-icon { width: 8px; height: 8px; border-radius: 2px; background: #5b46ff; }
.tool-chip.running .tool-chip-icon { animation: typingPulse 1.2s ease-in-out infinite; }
.tool-chip.done .tool-chip-icon { background: var(--green, #19a974); }
.tool-chip-status { color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; font-size: 10px; }
```

(f) **Cursor**:

```css
.chat-cursor { display: inline-block; width: 8px; height: 16px; margin-left: 2px; border-radius: 2px; background: #5b46ff; vertical-align: text-bottom; animation: typingPulse 1s ease-in-out infinite; }
```

- [ ] **Step 3: Verify build**

Run: `cd apps/web && npx tsc --noEmit`
Expected: errors only from leftover `AgentStatusCard`/`agentStatusCard` references (resolved in Task 8).

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/app/page.tsx apps/web/src/app/globals.css
git commit -m "feat(web): mount ProcessTrace + cursor slot, rebalance layout and type scale"
```

---

## Task 8: Frontend cleanup — remove AgentStatusCard + dead code

**Files:**
- Delete: `apps/web/src/components/generative-ui/agent-status-card.tsx`
- Modify: `apps/web/src/components/generative-ui/types.ts`
- Modify: `apps/web/src/components/generative-ui/registry.ts`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Delete the component and its registry/type/imports**

```bash
git rm apps/web/src/components/generative-ui/agent-status-card.tsx
```

- In `types.ts`: remove the `AgentStatusCardProps` Zod schema and its exported type.
- In `registry.ts`: remove the `agentStatusCard: "agentStatusCard",` entry from `GENERATIVE_UI_COMPONENTS`.
- In `use-risk-generative-ui.tsx`: confirm no remaining `AgentStatusCard` / `AgentStatusCardProps` imports (should already be removed in Task 5; remove any leftover).

- [ ] **Step 2: Remove dead CSS**

In `apps/web/src/app/globals.css`, delete the now-unused rules: `.agent-status-card`, `.agent-status-card.reasoning`, `.agent-status-card.approved`, `.agent-status-dot`, `.agent-status-card div`, `.agent-status-kicker`, `.agent-status-card strong`, `.agent-status-card span`, `.agent-status-card small`. Search for any keyframe used only by these rules; remove only if unreferenced elsewhere.

- [ ] **Step 3: Type-check + lint (must be fully clean now)**

Run: `cd apps/web && npx tsc --noEmit && npm run lint`
Expected: PASS — zero errors, no unused-import or no-undef warnings related to the removed code.

- [ ] **Step 4: Verify the unit tests still pass**

Run: `cd apps/web && npm run test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A apps/web/src/components/generative-ui apps/web/src/app/globals.css apps/web/src/hooks/use-risk-generative-ui.tsx
git commit -m "refactor(web): remove legacy AgentStatusCard and dead styles"
```

---

## Task 9: Backend — stop phase text bubbles, retire status card, sync contract (TDD)

**Files:**
- Modify: `apps/agent/main.py`
- Modify: `apps/agent/src/component_registry.py`
- Test: `apps/agent/tests/test_ui_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Add to `apps/agent/tests/test_ui_contracts.py`:

```python
from src.ui_event_contract import UI_EVENT_KINDS, UI_EVENT_PHASES  # noqa: E402


def test_agent_status_card_is_no_longer_a_controlled_component() -> None:
    from src.component_registry import CONTROLLED_COMPONENT_NAMES

    assert "agentStatusCard" not in CONTROLLED_COMPONENT_NAMES


def test_emit_ui_event_does_not_emit_progress_text_bubbles(monkeypatch) -> None:
    import asyncio
    import main

    dispatched: list[str] = []

    async def fake_dispatch(name, payload):  # noqa: ANN001
        dispatched.append(name)

    monkeypatch.setattr(main, "adispatch_custom_event", fake_dispatch)
    asyncio.run(main._emit_ui_event("query.started", "query", {"message": "hi"}))

    assert dispatched == ["risk_ui_event"]
    assert "manually_emit_message" not in dispatched
```

If `UI_EVENT_KINDS` / `UI_EVENT_PHASES` are not already exported from `src/ui_event_contract.py`, the import line will fail — that is the expected initial failure. (Adjust the import to whatever the module exposes; the test that matters is the two assertions below it.)

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/agent && python -m pytest tests/test_ui_contracts.py -v`
Expected: FAIL — `agentStatusCard` still in `CONTROLLED_COMPONENT_NAMES` and `manually_emit_message` still dispatched.

- [ ] **Step 3: Apply backend changes**

In `apps/agent/main.py`:
- In `_emit_ui_event`, remove the trailing two lines that build `message` and call `_emit_progress(message)`. The function now only dispatches `risk_ui_event`:

```python
async def _emit_ui_event(kind: UiEventKind, phase: UiEventPhase, payload: dict[str, Any]) -> None:
    event = build_ui_event(kind, phase, payload)
    with suppress(RuntimeError):
        await adispatch_custom_event("risk_ui_event", event.to_payload())
```

- Delete the `_emit_progress` function (now unused) and the `_agent_status_message` function.
- Delete the `AGENT_STATUS_CARD = "agentStatusCard"` constant.
- In `_execute_risk_query`, replace the status-card seed with an empty list:

```python
    messages: list[AnyMessage] = []
```

(Confirm `messages.extend(...)` / `messages.append(...)` calls below still operate on this list; they do.)

In `apps/agent/src/component_registry.py`:
- Remove the `"agentStatusCard",` entry from `CONTROLLED_COMPONENT_NAMES`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/agent && python -m pytest tests/ -v`
Expected: PASS — new contract tests green, and the existing `test_ui_contracts`, `test_approval_flow`, `test_visualization_mapper`, `test_config` still pass.

- [ ] **Step 5: Commit**

```bash
git add apps/agent/main.py apps/agent/src/component_registry.py apps/agent/tests/test_ui_contracts.py
git commit -m "refactor(agent): emit only structured risk_ui_event, retire status card"
```

---

## Task 10: Consistency restyle (approval card + follow-ups)

**Files:**
- Modify: `apps/web/src/app/globals.css` (and component files only if class names need adjusting)

- [ ] **Step 1: Align McpApprovalCard and FollowUpQuestions to the new system**

In `apps/web/src/app/globals.css`, update the approval-card and follow-up styles to match the ProcessTrace/ToolChip language: same border radius family (16px), brand-tinted gradients, `font-size: 13–14px`, and the shared `fadeUp` entrance. Reuse existing CSS variables (`--primary`, `--green`, `--muted`, `--border`). Do not change component markup unless a class is missing; prefer styling existing classes.

- [ ] **Step 2: Verify build + lint**

Run: `cd apps/web && npx tsc --noEmit && npm run lint`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/globals.css
git commit -m "style(web): align approval card and follow-ups with new chat system"
```

---

## Task 11: Final verification + cleanup inventory

**Files:** none (verification only)

- [ ] **Step 1: Full frontend gate**

Run: `cd apps/web && npm run test && npx tsc --noEmit && npm run lint && npm run build`
Expected: all PASS. Record the build output summary.

- [ ] **Step 2: Full backend gate**

Run: `cd apps/agent && python -m pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 3: Grep for leftover legacy references (must return nothing)**

```bash
cd apps/web && grep -rn "agentStatusCard\|AgentStatusCard\|setDashboardToolStatus\|DashboardToolStatusBridge\|_emit_progress\|manually_emit_message" src/ || echo "clean"
cd ../agent && grep -rn "agentStatusCard\|_agent_status_message\|_emit_progress\|AGENT_STATUS_CARD\|manually_emit_message" main.py src/ || echo "clean"
```
Expected: both print `clean`.

- [ ] **Step 4: Manual smoke test**

Run: `cd apps/web && npm run dev` (with the agent running per repo README).
Verify:
1. Send "What is the total exposure by country in 2026-Q2?" → ProcessTrace streams phases (Reasoning → … → Visuals rendered), then collapses to "Thought for Xs · N steps"; expanding it shows all steps.
2. Tool chips appear inline (running → done) and charts render in the left dashboard.
3. The dashboard timeline (left) shows the same steps as ProcessTrace.
4. Run the HITL approval prompt; the MCP approval card renders in the new style and the run resumes.
5. Bubbles/fonts are visibly larger; layout gives the chat more width.
6. No stray phase-text bubbles or old status card appear.

- [ ] **Step 5: Append a removed/kept inventory to the spec and commit**

Append a short "Cleanup inventory" section to `docs/superpowers/specs/2026-05-20-chat-experience-redesign-design.md` listing what was removed (AgentStatusCard, `_emit_progress`/`manually_emit_message` bubbles, `_agent_status_message`, `AGENT_STATUS_CARD`, dashboard-store timeline duplication, `setDashboardToolStatus`/`DashboardToolStatusBridge`) and what was kept and why.

```bash
git add docs/superpowers/specs/2026-05-20-chat-experience-redesign-design.md
git commit -m "docs: record chat redesign cleanup inventory"
```

---

## Self-Review notes

- **Spec coverage:** split layout kept (Tasks 5–6); collapsible Thinking card (Task 4); rebalance + type scale (Task 7); modernize-with-brand (Tasks 7, 10); `risk_ui_event` as source of truth (Tasks 2–3, 6); inline tool chips (Task 5); cursor (Task 7); consistency pass (Task 10); cleanup/dead-code + contract sync (Tasks 5, 6, 8, 9); error handling via `error.safe` (Tasks 2, 4); testing (Tasks 2, 9, 11); out-of-scope respected (no inline charts, no fake CoT).
- **Types consistent across tasks:** `applyUiEvent`, `startRun`, `finishRun`, `failRun`, `getProcessSnapshot`, `subscribeProcess`, `getRunDurationSeconds`, `ProcessStep` used identically in store, hook, ProcessTrace, and dashboard-stage.
- **Known verification dependency:** the exact `AgentSubscriber` callback names in `@ag-ui/client@0.0.52` are confirmed against CopilotKit v2 docs (`onCustomEvent`, `onRunStartedEvent`, `onRunFinalized`, `onRunFailed`); Task 3 Step 2 includes a fallback to read the installed `.d.ts` if a name differs.
