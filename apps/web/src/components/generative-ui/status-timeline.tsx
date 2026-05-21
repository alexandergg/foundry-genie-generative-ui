"use client";

import { useState } from "react";
import type { DashboardPhase } from "./dashboard-store";
import type { ProcessState } from "./process-store";
import { formatRunSummary } from "./process-summary";

const PHASE_LABELS: Record<DashboardPhase, string> = {
  idle: "Waiting",
  planning: "Planning",
  ready: "Ready",
};

export function formatDashboardPhase(phase: DashboardPhase) {
  return PHASE_LABELS[phase];
}

// Reasoning traces are short; cap defensively so a runaway run can't grow the panel unbounded.
const MAX_VISIBLE_STEPS = 12;

export function StatusTimeline({ process }: { process: ProcessState }) {
  const { steps, status } = process;
  const [open, setOpen] = useState(false);

  // Auto-expand while reasoning, auto-collapse when done; keep errors open. We
  // adjust during render on a status transition (React's recommended pattern)
  // so the user can still toggle manually between transitions.
  const [prevStatus, setPrevStatus] = useState(status);
  if (status !== prevStatus) {
    setPrevStatus(status);
    if (status === "running" || status === "error") setOpen(true);
    else if (status === "complete") setOpen(false);
  }

  if (steps.length === 0) {
    return null;
  }

  const latest = steps[steps.length - 1];
  const visible = steps.slice(-MAX_VISIBLE_STEPS);
  const glyph = status === "error" ? "error" : status === "running" ? "running" : "complete";
  const showSubtitle = !open && status === "running" && Boolean(latest?.detail);

  return (
    <div className={`reasoning-disclosure ${status}`}>
      <button type="button" className="reasoning-header" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span className={`reasoning-chevron ${open ? "open" : ""}`} aria-hidden="true" />
        <span className={`reasoning-glyph ${glyph}`} aria-hidden="true" />
        <span className="reasoning-title">{formatRunSummary(process)}</span>
        {showSubtitle ? <span className="reasoning-subtitle">{latest.detail}</span> : null}
      </button>

      {open ? (
        <ol className="status-timeline" aria-label="Agent run timeline">
          {visible.map((event) => (
            <li className={`timeline-step ${event.status}`} key={event.id}>
              <span className="timeline-dot" aria-hidden="true" />
              <div>
                <p>{event.label}</p>
                {event.detail ? <span>{event.detail}</span> : null}
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
