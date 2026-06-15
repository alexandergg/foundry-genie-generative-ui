import type { AgentSubscriber } from "@ag-ui/client";
import { applyUiEvent, failRun, finishRun, startRun } from "@/components/generative-ui/process-store";
import { getDashboardSnapshot, setDashboardPlanning } from "@/components/generative-ui/dashboard-store";

export const RISK_UI_EVENT = "risk_ui_event";

export interface RiskUiSubscriberHandlers {
  startRun: () => void;
  applyUiEvent: (value: unknown) => void;
  finishRun: () => void;
  failRun: () => void;
  onGovernedFlowStarted: () => void;
}

// A governed Genie flow is underway and visuals are coming. If the canvas is
// still empty, switch it to the planning skeleton so the live status timeline is
// visible from the moment the supervisor commits to the governed route, before
// the query lands. Accumulated dashboards keep their visuals (the timeline
// already renders above them), so we never wipe prior results mid-conversation.
function defaultOnGovernedFlowStarted(): void {
  if (getDashboardSnapshot().visuals.length === 0) setDashboardPlanning();
}

const defaultHandlers: RiskUiSubscriberHandlers = {
  startRun,
  applyUiEvent,
  finishRun,
  failRun,
  onGovernedFlowStarted: defaultOnGovernedFlowStarted,
};

// Earliest signals that governed visuals are on the way: `plan.created` once the
// supervisor commits to the risk-data route, and `query.started` for the direct
// `approve <id>` path that skips planning. We deliberately do NOT trigger on
// run-start or `reasoning.started`, which also fire for greetings/direct answers
// and would strand a loading skeleton on a turn that produces no visuals.
const GOVERNED_FLOW_KINDS = new Set(["plan.created", "query.started"]);

function signalsGovernedFlow(value: unknown): boolean {
  if (typeof value !== "object" || value === null) return false;
  const kind = (value as { kind?: unknown }).kind;
  return typeof kind === "string" && GOVERNED_FLOW_KINDS.has(kind);
}

/**
 * Build the AG-UI subscriber that drives the process-store from the agent's
 * event stream. Handlers are injectable so the routing can be unit-tested in a
 * node environment without React or a live agent.
 */
export function makeRiskUiSubscriber(handlers: RiskUiSubscriberHandlers = defaultHandlers): AgentSubscriber {
  return {
    onRunStartedEvent: () => handlers.startRun(),
    onCustomEvent: ({ event }) => {
      if (event.name !== RISK_UI_EVENT) return;
      handlers.applyUiEvent(event.value);
      if (signalsGovernedFlow(event.value)) handlers.onGovernedFlowStarted();
    },
    onRunFinalized: () => handlers.finishRun(),
    onRunFailed: () => handlers.failRun(),
  };
}
