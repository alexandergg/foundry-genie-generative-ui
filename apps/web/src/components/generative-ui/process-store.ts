import { UiEventEnvelopeV1, type UiEventKind, type UiEventPhase } from "./contracts";

export type ProcessStepStatus = "active" | "complete" | "error";
export type ProcessRunStatus = "idle" | "running" | "complete" | "error";

export type ProcessStep = {
  id: string;
  kind: UiEventKind;
  phase: UiEventPhase;
  label: string;
  detail?: string;
  status: ProcessStepStatus;
  at: number;
};

export type ProcessState = {
  status: ProcessRunStatus;
  steps: ProcessStep[];
  startedAt?: number;
  finishedAt?: number;
};

const KIND_LABEL: Record<UiEventKind, string> = {
  "reasoning.started": "Reasoning",
  "reasoning.completed": "Reasoning",
  "plan.created": "Planning the analysis",
  "approval.requested": "Awaiting approval",
  "approval.updated": "Approval updated",
  "query.started": "Querying governed data",
  "query.completed": "Query complete",
  "normalization.started": "Normalizing results",
  "normalization.completed": "Normalization complete",
  "visualization.proposed": "Preparing visuals",
  "visualization.rendered": "Visuals rendered",
  "provenance.attached": "Provenance attached",
  "followups.suggested": "Suggested follow-ups",
  "error.safe": "Stopped safely",
};

const TERMINAL_KINDS = new Set<UiEventKind>([
  "reasoning.completed",
  "query.completed",
  "normalization.completed",
  "visualization.rendered",
  "approval.updated",
  "provenance.attached",
  "followups.suggested",
]);

let state: ProcessState = { status: "idle", steps: [] };
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function completeActive(steps: ProcessStep[]): ProcessStep[] {
  return steps.map((step) => (step.status === "active" ? { ...step, status: "complete" } : step));
}

export function subscribeProcess(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getProcessSnapshot(): ProcessState {
  return state;
}

export function resetProcessStore() {
  state = { status: "idle", steps: [] };
  emit();
}

export function startRun() {
  state = { status: "running", steps: [], startedAt: Date.now() };
  emit();
}

export function applyUiEvent(raw: unknown) {
  const parsed = UiEventEnvelopeV1.safeParse(raw);
  if (!parsed.success) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[process-store] dropped malformed risk_ui_event", parsed.error.issues);
    }
    return;
  }
  const envelope = parsed.data;
  const payload = (envelope.payload ?? {}) as { message?: string };
  const isError = envelope.kind === "error.safe";
  const step: ProcessStep = {
    id: envelope.eventId,
    kind: envelope.kind,
    phase: envelope.phase,
    label: KIND_LABEL[envelope.kind],
    detail: payload.message,
    status: isError ? "error" : TERMINAL_KINDS.has(envelope.kind) ? "complete" : "active",
    at: Date.now(),
  };
  state = {
    ...state,
    status: isError ? "error" : state.status,
    steps: [...completeActive(state.steps), step],
  };
  emit();
}

export function finishRun() {
  if (state.status === "error") {
    state = { ...state, finishedAt: state.finishedAt ?? Date.now() };
    emit();
    return;
  }
  state = {
    ...state,
    status: "complete",
    steps: completeActive(state.steps),
    finishedAt: Date.now(),
  };
  emit();
}

export function failRun() {
  state = { ...state, status: "error", finishedAt: Date.now() };
  emit();
}

export function getRunDurationSeconds(): number | undefined {
  if (state.startedAt == null || state.finishedAt == null) return undefined;
  return Math.max(0, Math.round((state.finishedAt - state.startedAt) / 1000));
}
