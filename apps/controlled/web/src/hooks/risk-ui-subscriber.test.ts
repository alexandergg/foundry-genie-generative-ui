import { describe, it, expect, vi, beforeEach } from "vitest";
import { makeRiskUiSubscriber } from "./risk-ui-subscriber";
import { addVisual, getDashboardSnapshot, resetDashboardStore } from "@/components/generative-ui/dashboard-store";
import type { VisualSpec } from "@/components/generative-ui/dataset-types";

function spyHandlers() {
  return {
    startRun: vi.fn(),
    applyUiEvent: vi.fn(),
    finishRun: vi.fn(),
    failRun: vi.fn(),
    onGovernedFlowStarted: vi.fn(),
  };
}

function emitCustom(value: unknown, name = "risk_ui_event") {
  const handlers = spyHandlers();
  makeRiskUiSubscriber(handlers).onCustomEvent?.({ event: { name, value } } as never);
  return handlers;
}

describe("makeRiskUiSubscriber", () => {
  it("starts a run on onRunStartedEvent", () => {
    const handlers = spyHandlers();
    makeRiskUiSubscriber(handlers).onRunStartedEvent?.({} as never);
    expect(handlers.startRun).toHaveBeenCalledTimes(1);
  });

  it("applies a risk_ui_event custom event value to the store", () => {
    const handlers = emitCustom({ kind: "query.started", phase: "query" });
    expect(handlers.applyUiEvent).toHaveBeenCalledTimes(1);
    expect(handlers.applyUiEvent).toHaveBeenCalledWith({ kind: "query.started", phase: "query" });
  });

  it("signals onGovernedFlowStarted on plan.created and query.started, not on plain reasoning", () => {
    expect(emitCustom({ kind: "plan.created", phase: "supervise" }).onGovernedFlowStarted).toHaveBeenCalledTimes(1);
    expect(emitCustom({ kind: "query.started", phase: "query" }).onGovernedFlowStarted).toHaveBeenCalledTimes(1);
    expect(emitCustom({ kind: "reasoning.started", phase: "supervise" }).onGovernedFlowStarted).not.toHaveBeenCalled();
  });

  it("ignores custom events with a different name", () => {
    const handlers = emitCustom({ kind: "query.started" }, "other_event");
    expect(handlers.applyUiEvent).not.toHaveBeenCalled();
    expect(handlers.onGovernedFlowStarted).not.toHaveBeenCalled();
  });

  it("finishes the run on onRunFinalized", () => {
    const handlers = spyHandlers();
    makeRiskUiSubscriber(handlers).onRunFinalized?.({} as never);
    expect(handlers.finishRun).toHaveBeenCalledTimes(1);
  });

  it("fails the run on onRunFailed", () => {
    const handlers = spyHandlers();
    makeRiskUiSubscriber(handlers).onRunFailed?.({} as never);
    expect(handlers.failRun).toHaveBeenCalledTimes(1);
  });
});

describe("default onGovernedFlowStarted (planning skeleton)", () => {
  beforeEach(() => resetDashboardStore());

  function spec(over: Partial<VisualSpec>): VisualSpec {
    return { id: "v", datasetId: "a", type: "barChartCard", title: "T", order: 0, ...over };
  }

  function fire(kind: string) {
    makeRiskUiSubscriber().onCustomEvent?.({
      event: { name: "risk_ui_event", value: { kind, phase: "supervise" } },
    } as never);
  }

  it("switches an empty canvas to planning on plan.created, before the query runs", () => {
    fire("plan.created");
    expect(getDashboardSnapshot().phase).toBe("planning");
  });

  it("switches an empty canvas to planning on query.started", () => {
    fire("query.started");
    expect(getDashboardSnapshot().phase).toBe("planning");
  });

  it("keeps accumulated visuals instead of wiping them on a follow-up query", () => {
    addVisual(spec({ id: "v1" }));
    fire("query.started");
    const snapshot = getDashboardSnapshot();
    expect(snapshot.phase).toBe("ready");
    expect(snapshot.visuals).toHaveLength(1);
  });
});
