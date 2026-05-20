import type { DashboardPhase } from "./dashboard-store";
import type { ProcessStep } from "./process-store";

const PHASE_LABELS: Record<DashboardPhase, string> = {
  idle: "Waiting",
  planning: "Planning",
  approval: "Approval",
  querying: "Querying",
  normalizing: "Normalizing",
  rendering: "Rendering",
  ready: "Ready",
  error: "Needs attention",
};

export function formatDashboardPhase(phase: DashboardPhase) {
  return PHASE_LABELS[phase];
}

export function StatusTimeline({ events }: { events: ProcessStep[] }) {
  if (events.length === 0) {
    return null;
  }

  return (
    <ol className="status-timeline" aria-label="Agent run timeline">
      {events.slice(-5).map((event) => (
        <li className={`timeline-step ${event.status}`} key={event.id}>
          <span className="timeline-dot" aria-hidden="true" />
          <div>
            <p>{event.label}</p>
            {event.detail ? <span>{event.detail}</span> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
