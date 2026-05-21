import type { AgentSubscriber } from "@ag-ui/client";
import { applyUiEvent, failRun, finishRun, startRun } from "@/components/generative-ui/process-store";

export const RISK_UI_EVENT = "risk_ui_event";

export interface RiskUiSubscriberHandlers {
  startRun: () => void;
  applyUiEvent: (value: unknown) => void;
  finishRun: () => void;
  failRun: () => void;
}

const defaultHandlers: RiskUiSubscriberHandlers = { startRun, applyUiEvent, finishRun, failRun };

/**
 * Build the AG-UI subscriber that drives the process-store from the agent's
 * event stream. Handlers are injectable so the routing can be unit-tested in a
 * node environment without React or a live agent.
 */
export function makeRiskUiSubscriber(handlers: RiskUiSubscriberHandlers = defaultHandlers): AgentSubscriber {
  return {
    onRunStartedEvent: () => handlers.startRun(),
    onCustomEvent: ({ event }) => {
      if (event.name === RISK_UI_EVENT) handlers.applyUiEvent(event.value);
    },
    onRunFinalized: () => handlers.finishRun(),
    onRunFailed: () => handlers.failRun(),
  };
}
