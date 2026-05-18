import { z } from "zod";

export const Format = z.enum(["currency", "number", "percent", "text"]).default("number");
export type Format = z.infer<typeof Format>;

export const KpiStripProps = z.object({
  items: z.array(z.object({
    label: z.string(),
    value: z.union([z.string(), z.number()]),
    format: Format.optional(),
  })),
});
export type KpiStripProps = z.infer<typeof KpiStripProps>;

const ChartRow = z.record(z.union([z.string(), z.number(), z.null()]));

export const BarChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKey: z.string(),
  valueFormat: Format.optional(),
});
export type BarChartCardProps = z.infer<typeof BarChartCardProps>;

export const LineAreaChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKeys: z.array(z.string()).min(1).max(3),
  valueFormat: Format.optional(),
});
export type LineAreaChartCardProps = z.infer<typeof LineAreaChartCardProps>;

export const DonutChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  labelKey: z.string(),
  valueKey: z.string(),
  valueFormat: Format.optional(),
});
export type DonutChartCardProps = z.infer<typeof DonutChartCardProps>;

export const MetricComparisonChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKeys: z.array(z.string()).min(2).max(3),
  valueFormat: Format.optional(),
});
export type MetricComparisonChartCardProps = z.infer<typeof MetricComparisonChartCardProps>;

export const InsightTableProps = z.object({
  title: z.string(),
  columns: z.array(z.string()),
  rows: z.array(z.record(z.union([z.string(), z.number(), z.null()]))),
});
export type InsightTableProps = z.infer<typeof InsightTableProps>;

export const RiskNarrativeCardProps = z.object({
  title: z.string(),
  answer: z.string(),
  assumptions: z.array(z.string()).optional(),
});
export type RiskNarrativeCardProps = z.infer<typeof RiskNarrativeCardProps>;

export const VisualizationPlanProps = z.object({
  approach: z.string(),
  technology: z.string(),
  key_elements: z.array(z.string()),
});
export type VisualizationPlanProps = z.infer<typeof VisualizationPlanProps>;

export const WarehouseStatusCardProps = z.object({
  warehouseName: z.string(),
  status: z.string(),
});
export type WarehouseStatusCardProps = z.infer<typeof WarehouseStatusCardProps>;

export const McpApprovalCardProps = z.object({
  requestId: z.string(),
  question: z.string(),
  dataSource: z.string(),
  purpose: z.string(),
  approvalCommand: z.string(),
});
export type McpApprovalCardProps = z.infer<typeof McpApprovalCardProps>;

export const FollowUpQuestionsProps = z.object({
  title: z.string(),
  questions: z.array(z.string()).min(1).max(4),
});
export type FollowUpQuestionsProps = z.infer<typeof FollowUpQuestionsProps>;
