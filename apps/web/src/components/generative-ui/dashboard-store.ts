import type { VisualSpec, DerivableVisualType } from "./dataset-types";

export type DashboardPhase = "idle" | "planning" | "ready";

export type DashboardState = {
  phase: DashboardPhase;
  visuals: VisualSpec[];
};

let state: DashboardState = { phase: "idle", visuals: [] };
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function sortByOrder(v: VisualSpec[]): VisualSpec[] {
  return [...v].sort((a, b) => a.order - b.order);
}

export function subscribeDashboard(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getDashboardSnapshot(): DashboardState {
  return state;
}

export function setDashboardPlanning() {
  state = { phase: "planning", visuals: [] };
  emit();
}

export function addVisual(spec: VisualSpec) {
  const rest = state.visuals.filter((v) => v.id !== spec.id);
  state = { phase: "ready", visuals: sortByOrder([...rest, spec]) };
  emit();
}

export function removeVisual(id: string) {
  state = { ...state, visuals: state.visuals.filter((v) => v.id !== id) };
  emit();
}

export function changeVisualType(id: string, type: DerivableVisualType) {
  state = { ...state, visuals: state.visuals.map((v) => (v.id === id ? { ...v, type } : v)) };
  emit();
}

export function reorderVisuals(orderedIds: string[]) {
  const index = new Map(orderedIds.map((id, i) => [id, i]));
  state = {
    ...state,
    visuals: [...state.visuals].sort((a, b) => (index.get(a.id) ?? 0) - (index.get(b.id) ?? 0)).map((v, i) => ({ ...v, order: i })),
  };
  emit();
}

export function removeVisualsForDataset(datasetId: string) {
  state = { ...state, visuals: state.visuals.filter((v) => v.datasetId !== datasetId) };
  emit();
}

export function clearDashboard() {
  state = { phase: "idle", visuals: [] };
  emit();
}

export function resetDashboardStore() {
  state = { phase: "idle", visuals: [] };
  emit();
}
