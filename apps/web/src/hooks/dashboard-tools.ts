import type { Dataset, DerivableVisualType, VisualSpec } from "@/components/generative-ui/dataset-types";

export type CacheDatasetArgs = Omit<Dataset, "createdAt" | "traceId"> & { traceId?: string };
export type AddVisualArgs = Omit<VisualSpec, "id" | "order">;

export function datasetFromArgs(args: CacheDatasetArgs): Dataset {
  return { ...args, createdAt: Date.now() };
}

// Deterministic visual id so re-renders of the same tool call replace rather
// than duplicate (DashboardStore.addVisual replaces by id).
export function visualIdFor(args: AddVisualArgs): string {
  const measure = Array.isArray(args.measure) ? args.measure.join("_") : args.measure ?? "v";
  return `vis-${args.datasetId}-${args.type}-${args.dimension ?? "x"}-${measure}`;
}

const orderById = new Map<string, number>();
let orderSeq = 0;

export function orderFor(id: string): number {
  if (!orderById.has(id)) orderById.set(id, orderSeq++);
  return orderById.get(id) as number;
}

export function visualSpecFromArgs(args: AddVisualArgs): VisualSpec {
  const id = visualIdFor(args);
  return { ...args, id, order: orderFor(id) };
}

export type { DerivableVisualType };
