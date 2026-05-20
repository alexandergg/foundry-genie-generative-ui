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
