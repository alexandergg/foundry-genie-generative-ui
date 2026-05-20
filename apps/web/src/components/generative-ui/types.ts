import { z } from "zod";

export const Format = z.enum(["currency", "number", "percent", "text"]).default("number");
export type Format = z.infer<typeof Format>;

const ChartRow = z.record(z.union([z.string(), z.number(), z.null()]));

export const VisualProvenance = z.object({
  visualId: z.string(),
  source: z.string(),
  generatedAt: z.string(),
  rowCount: z.number(),
  approvalRequestId: z.string().optional(),
  traceId: z.string().optional(),
  warnings: z.array(z.object({ code: z.string(), message: z.string() })).default([]),
});
export type VisualProvenance = z.infer<typeof VisualProvenance>;

export const KpiStripProps = z.object({
  items: z.array(z.object({
    label: z.string(),
    value: z.union([z.string(), z.number()]),
    format: Format.optional(),
    status: z.enum(["stable", "attention", "critical"]).optional(),
    delta: z.string().optional(),
  })),
  provenance: VisualProvenance.optional(),
});
export type KpiStripProps = z.infer<typeof KpiStripProps>;

export const BarChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKey: z.string(),
  valueFormat: Format.optional(),
  provenance: VisualProvenance.optional(),
});
export type BarChartCardProps = z.infer<typeof BarChartCardProps>;

export const LineAreaChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKeys: z.array(z.string()).min(1).max(3),
  valueFormat: Format.optional(),
  provenance: VisualProvenance.optional(),
});
export type LineAreaChartCardProps = z.infer<typeof LineAreaChartCardProps>;

export const DonutChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  labelKey: z.string(),
  valueKey: z.string(),
  valueFormat: Format.optional(),
  provenance: VisualProvenance.optional(),
});
export type DonutChartCardProps = z.infer<typeof DonutChartCardProps>;

export const MetricComparisonChartCardProps = z.object({
  title: z.string(),
  data: z.array(ChartRow),
  xKey: z.string(),
  yKeys: z.array(z.string()).min(2).max(3),
  valueFormat: Format.optional(),
  provenance: VisualProvenance.optional(),
});
export type MetricComparisonChartCardProps = z.infer<typeof MetricComparisonChartCardProps>;

export const InsightTableProps = z.object({
  title: z.string(),
  columns: z.array(z.string()),
  rows: z.array(z.record(z.union([z.string(), z.number(), z.null()]))),
  provenance: VisualProvenance.optional(),
});
export type InsightTableProps = z.infer<typeof InsightTableProps>;

export const RiskNarrativeCardProps = z.object({
  title: z.string(),
  answer: z.string(),
  assumptions: z.array(z.string()).optional(),
  provenance: VisualProvenance.optional(),
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

export const PolicyBreachCardProps = z.object({
  title: z.string(),
  severity: z.enum(["stable", "attention", "critical"]),
  summary: z.string(),
  metricLabel: z.string(),
  metricValue: z.union([z.string(), z.number()]),
  recommendation: z.string(),
  provenance: VisualProvenance.optional(),
});
export type PolicyBreachCardProps = z.infer<typeof PolicyBreachCardProps>;

export const McpApprovalCardProps = z.object({
  requestId: z.string(),
  question: z.string(),
  dataSource: z.string(),
  purpose: z.string(),
  approvalCommand: z.string(),
  rejectCommand: z.string().optional(),
  reviseCommandPrefix: z.string().optional(),
  expiresAt: z.string().optional(),
  auditId: z.string().optional(),
});
export type McpApprovalCardProps = z.infer<typeof McpApprovalCardProps>;

export const FollowUpQuestionsProps = z.object({
  title: z.string(),
  questions: z.array(z.string()).min(1).max(4),
});
export type FollowUpQuestionsProps = z.infer<typeof FollowUpQuestionsProps>;
