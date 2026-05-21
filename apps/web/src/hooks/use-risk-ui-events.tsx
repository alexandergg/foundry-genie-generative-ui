"use client";

import { useEffect } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import { makeRiskUiSubscriber } from "./risk-ui-subscriber";

export function useRiskUiEvents() {
  const { agent } = useAgent();

  useEffect(() => {
    const { unsubscribe } = agent.subscribe(makeRiskUiSubscriber());
    return () => unsubscribe();
  }, [agent]);
}
