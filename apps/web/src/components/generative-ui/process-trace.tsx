"use client";

import { useSyncExternalStore, useState, useEffect } from "react";
import {
  subscribeProcess,
  getProcessSnapshot,
  getRunDurationSeconds,
  type ProcessStep,
} from "./process-store";

function StepRow({ step }: { step: ProcessStep }) {
  return (
    <li className={`process-step ${step.status}`}>
      <span className="process-step-dot" aria-hidden="true" />
      <div>
        <p>{step.label}</p>
        {step.detail ? <span>{step.detail}</span> : null}
      </div>
    </li>
  );
}

export function ProcessTrace() {
  const state = useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot);
  const [open, setOpen] = useState(true);
  const isRunning = state.status === "running";

  // Auto-expand while running; auto-collapse shortly after completion.
  useEffect(() => {
    if (isRunning) {
      const timer = setTimeout(() => setOpen(true), 0);
      return () => clearTimeout(timer);
    }
    if (state.status === "complete" || state.status === "error") {
      const timer = setTimeout(() => setOpen(false), 900);
      return () => clearTimeout(timer);
    }
  }, [isRunning, state.status]);

  if (state.status === "idle" || state.steps.length === 0) return null;

  const duration = getRunDurationSeconds();
  const summary = isRunning
    ? "Thinking…"
    : state.status === "error"
      ? `Stopped · ${state.steps.length} steps`
      : `Thought${duration != null ? ` for ${duration}s` : ""} · ${state.steps.length} steps`;

  return (
    <section className={`process-trace ${state.status}`} aria-label="Agent process">
      <button
        type="button"
        className="process-trace-header"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className={`process-trace-indicator ${isRunning ? "live" : ""}`} aria-hidden="true" />
        <strong>{summary}</strong>
        <span className="process-trace-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <ol className="process-trace-steps">
          {state.steps.map((step) => (
            <StepRow key={step.id} step={step} />
          ))}
        </ol>
      ) : null}
    </section>
  );
}
