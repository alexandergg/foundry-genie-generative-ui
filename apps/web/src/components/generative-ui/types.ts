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
