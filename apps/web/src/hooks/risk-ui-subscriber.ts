import type { AgentSubscriber } from "@ag-ui/client";
import { applyUiEvent, failRun, finishRun, startRun } from "@/components/generative-ui/process-store";
import { getDashboardSnapshot, setDashboardPlanning } from "@/components/generative-ui/dashboard-store";

export const RISK_UI_EVENT = "risk_ui_event";

export interface RiskUiSubscriberHandlers {
  startRun: () => void;
  applyUiEvent: (value: unknown) => void;
  finishRun: () => void;
  failRun: () => void;
  onQueryStarted: () => void;
}

// `query.started` is the agent's signal that a governed Genie query is running
// and visuals are coming. If the canvas is still empty, switch it to the planning
// skeleton so the live status timeline is visible. Accumulated dashboards keep
// their visuals (the timeline already renders above them), so we never wipe prior
// results mid-conversation.
function defaultOnQueryStarted(): void {
  if (getDashboardSnapshot().visuals.length === 0) setDashboardPlanning();
}

const defaultHandlers: RiskUiSubscriberHandlers = {
  startRun,
  applyUiEvent,
  finishRun,
  failRun,
  onQueryStarted: defaultOnQueryStarted,
};

function isQueryStarted(value: unknown): boolean {
  return typeof value === "object" && value !== null && (value as { kind?: unknown }).kind === "query.started";
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
      if (isQueryStarted(event.value)) handlers.onQueryStarted();
    },
    onRunFinalized: () => handlers.finishRun(),
    onRunFailed: () => handlers.failRun(),
  };
}
