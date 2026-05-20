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
