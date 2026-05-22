import { z } from "zod";

export const ColumnRole = z.enum(["dimension", "measure"]);
export type ColumnRole = z.infer<typeof ColumnRole>;

export const ColumnFormat = z.enum(["currency", "number", "percent", "text"]);
export type ColumnFormat = z.infer<typeof ColumnFormat>;

export const Column = z.object({
  key: z.string(),
  label: z.string(),
  role: ColumnRole,
  format: ColumnFormat.optional(),
});
export type Column = z.infer<typeof Column>;

export const DatasetRow = z.record(z.union([z.string(), z.number(), z.null()]));
export type DatasetRow = z.infer<typeof DatasetRow>;

// Governance trail for one Genie result. Shared by every visual derived from
// the dataset; each card adds its own `visualId` when it renders the footer.
export const DatasetProvenance = z.object({
  source: z.string(),
  generatedAt: z.string(),
  rowCount: z.number(),
  approvalRequestId: z.string().optional(),
  traceId: z.string().optional(),
  warnings: z.array(z.object({ code: z.string(), message: z.string() })).default([]),
});
export type DatasetProvenance = z.infer<typeof DatasetProvenance>;

export const Dataset = z.object({
  id: z.string(),
  title: z.string(),
  question: z.string(),
  columns: z.array(Column),
  rows: z.array(DatasetRow),
  // Genie's prose answer behind the dataset, rendered as the executive summary.
  answer: z.string().optional(),
  traceId: z.string().optional(),
  provenance: DatasetProvenance.optional(),
  createdAt: z.number(),
});
export type Dataset = z.infer<typeof Dataset>;

export type DatasetSummary = {
  id: string;
  title: string;
  rowCount: number;
  columns: Column[];
};

// Visuals derived from a dataset's columns/rows (dimension + measure).
export const VISUAL_TYPES = [
  "barChartCard",
  "lineAreaChartCard",
  "donutChartCard",
  "metricComparisonChartCard",
  "insightTable",
] as const;
export type DerivableVisualType = (typeof VISUAL_TYPES)[number];

// Executive summary is a prose card, not derived from columns — addable and
// renderable like a visual, but not a valid changeVisualType target.
export const NARRATIVE_VISUAL_TYPE = "riskNarrativeCard" as const;
export const ALL_VISUAL_TYPES = [...VISUAL_TYPES, NARRATIVE_VISUAL_TYPE] as const;
export type VisualType = (typeof ALL_VISUAL_TYPES)[number];

export const VisualSpec = z.object({
  id: z.string(),
  datasetId: z.string(),
  type: z.enum(ALL_VISUAL_TYPES),
  dimension: z.string().optional(),
  measure: z.union([z.string(), z.array(z.string())]).optional(),
  title: z.string(),
  order: z.number(),
});
export type VisualSpec = z.infer<typeof VisualSpec>;
