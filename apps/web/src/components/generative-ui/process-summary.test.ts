import { describe, expect, it } from "vitest";
import { formatRunSummary } from "./process-summary";
import type { ProcessState, ProcessStep } from "./process-store";

function steps(n: number): ProcessStep[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `s${i}`,
    kind: "reasoning.started" as const,
    phase: "supervise" as const,
    label: "Reasoning",
    status: "complete" as const,
    at: 0,
  }));
}

describe("formatRunSummary", () => {
  it("shows a thinking label while running", () => {
    expect(formatRunSummary({ status: "running", steps: steps(3), startedAt: 0 })).toBe("Reasoning…");
  });

  it("shows duration and step count when complete", () => {
    const process: ProcessState = { status: "complete", steps: steps(5), startedAt: 0, finishedAt: 4000 };
    expect(formatRunSummary(process)).toBe("Reasoned for 4s · 5 steps");
  });

  it("rounds sub-second runs up to 1s and singularizes one step", () => {
    const process: ProcessState = { status: "complete", steps: steps(1), startedAt: 0, finishedAt: 200 };
    expect(formatRunSummary(process)).toBe("Reasoned for 1s · 1 step");
  });

  it("labels a safe stop on error", () => {
    expect(formatRunSummary({ status: "error", steps: steps(3), startedAt: 0, finishedAt: 1000 })).toBe(
      "Stopped safely · 3 steps",
    );
  });
});
