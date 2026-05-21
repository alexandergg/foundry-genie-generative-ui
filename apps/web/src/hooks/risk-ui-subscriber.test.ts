import { describe, it, expect, vi } from "vitest";
import { makeRiskUiSubscriber } from "./risk-ui-subscriber";

function spyHandlers() {
  return {
    startRun: vi.fn(),
    applyUiEvent: vi.fn(),
    finishRun: vi.fn(),
    failRun: vi.fn(),
  };
}

describe("makeRiskUiSubscriber", () => {
  it("starts a run on onRunStartedEvent", () => {
    const handlers = spyHandlers();
    makeRiskUiSubscriber(handlers).onRunStartedEvent?.({} as never);
    expect(handlers.startRun).toHaveBeenCalledTimes(1);
  });

  it("applies a risk_ui_event custom event value to the store", () => {
    const handlers = spyHandlers();
    const value = { kind: "query.started", phase: "query" };
    makeRiskUiSubscriber(handlers).onCustomEvent?.({ event: { name: "risk_ui_event", value } } as never);
    expect(handlers.applyUiEvent).toHaveBeenCalledTimes(1);
    expect(handlers.applyUiEvent).toHaveBeenCalledWith(value);
  });

  it("ignores custom events with a different name", () => {
    const handlers = spyHandlers();
    makeRiskUiSubscriber(handlers).onCustomEvent?.({ event: { name: "other_event", value: { kind: "x" } } } as never);
    expect(handlers.applyUiEvent).not.toHaveBeenCalled();
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
