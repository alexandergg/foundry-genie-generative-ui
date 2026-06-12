import { z } from "zod";
import {
  Column,
  DatasetRow,
  DatasetProvenance,
  VISUAL_TYPES,
  ALL_VISUAL_TYPES,
  type Dataset,
  type DerivableVisualType,
  type VisualSpec,
} from "@/components/generative-ui/dataset-types";

// Tool-call parameter schemas. CopilotKit hands the bridges the raw streamed
// JSON (it does NOT parse against the schema passed to useRenderTool), so these
// are both advertised to the agent AND enforced on the incoming args before any
// store mutation. Validating here is what actually applies the defaults/coercions
// (e.g. provenance.warnings -> []) and rejects partial mid-stream payloads.
export const CacheDatasetParams = z.object({
  id: z.string(),
  title: z.string(),
  question: z.string(),
  columns: z.array(Column),
  rows: z.array(DatasetRow),
  answer: z.string().optional(),
  traceId: z.string().optional(),
  provenance: DatasetProvenance.optional(),
});

export const AddVisualParams = z.object({
  datasetId: z.string(),
  type: z.enum(ALL_VISUAL_TYPES),
  dimension: z.string().optional(),
  measure: z.union([z.string(), z.array(z.string())]).optional(),
  title: z.string(),
});

export const RemoveVisualParams = z.object({ id: z.string() });
export const ChangeVisualTypeParams = z.object({ id: z.string(), type: z.enum(VISUAL_TYPES) });
export const ReorderVisualsParams = z.object({ orderedIds: z.array(z.string()) });
// View tools: `id` is required-but-nullable (the agent sends {"id": null} to clear),
// so a partial mid-stream `{}` payload fails the parse instead of clearing early.
export const SpotlightVisualParams = z.object({ id: z.string().nullable() });
export const SetPresentationModeParams = z.object({ enabled: z.boolean() });

export type CacheDatasetArgs = z.infer<typeof CacheDatasetParams>;
export type AddVisualArgs = z.infer<typeof AddVisualParams>;

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

// Validate-then-map helpers. Each returns null when the (possibly mid-stream or
// malformed) args don't satisfy the schema, so the caller skips the mutation.
export function safeDatasetFromArgs(raw: unknown): Dataset | null {
  const parsed = CacheDatasetParams.safeParse(raw);
  return parsed.success ? { ...parsed.data, createdAt: Date.now() } : null;
}

export function safeVisualSpecFromArgs(raw: unknown): VisualSpec | null {
  const parsed = AddVisualParams.safeParse(raw);
  if (!parsed.success) return null;
  const id = visualIdFor(parsed.data);
  return { ...parsed.data, id, order: orderFor(id) };
}

export type { DerivableVisualType };
