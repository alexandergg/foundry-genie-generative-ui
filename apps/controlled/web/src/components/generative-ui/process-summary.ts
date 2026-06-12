import type { ProcessState } from "./process-store";

/** Header text for the collapsible reasoning disclosure, driven by run status. */
export function formatRunSummary(process: ProcessState): string {
  const count = process.steps.length;
  const steps = `${count} step${count === 1 ? "" : "s"}`;
  switch (process.status) {
    case "running":
      return "Reasoning…";
    case "error":
      return `Stopped safely · ${steps}`;
    case "complete": {
      const ms = (process.finishedAt ?? 0) - (process.startedAt ?? 0);
      const secs = Math.max(1, Math.round(ms / 1000));
      return `Reasoned for ${secs}s · ${steps}`;
    }
    default:
      return `Agent activity · ${steps}`;
  }
}
