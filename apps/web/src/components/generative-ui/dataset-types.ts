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

export const Dataset = z.object({
  id: z.string(),
  title: z.string(),
  question: z.string(),
  columns: z.array(Column),
  rows: z.array(DatasetRow),
  traceId: z.string().optional(),
  createdAt: z.number(),
});
export type Dataset = z.infer<typeof Dataset>;

export type DatasetSummary = {
  id: string;
  title: string;
  rowCount: number;
  columns: Column[];
};

export const VISUAL_TYPES = [
  "barChartCard",
  "lineAreaChartCard",
  "donutChartCard",
  "metricComparisonChartCard",
  "insightTable",
] as const;
export type DerivableVisualType = (typeof VISUAL_TYPES)[number];

export const VisualSpec = z.object({
  id: z.string(),
  datasetId: z.string(),
  type: z.enum(VISUAL_TYPES),
  dimension: z.string().optional(),
  measure: z.union([z.string(), z.array(z.string())]).optional(),
  title: z.string(),
  order: z.number(),
});
export type VisualSpec = z.infer<typeof VisualSpec>;
