export const GENERATIVE_UI_COMPONENTS = {
  kpiStrip: "kpiStrip",
  barChartCard: "barChartCard",
  lineAreaChartCard: "lineAreaChartCard",
  donutChartCard: "donutChartCard",
  metricComparisonChartCard: "metricComparisonChartCard",
  insightTable: "insightTable",
  riskNarrativeCard: "riskNarrativeCard",
  warehouseStatusCard: "warehouseStatusCard",
  policyBreachCard: "policyBreachCard",
  mcpApprovalCard: "mcpApprovalCard",
  followUpQuestions: "followUpQuestions",
  planVisualization: "plan_visualization",
} as const;

export const DASHBOARD_VISUAL_TYPES = [
  GENERATIVE_UI_COMPONENTS.riskNarrativeCard,
  GENERATIVE_UI_COMPONENTS.kpiStrip,
  GENERATIVE_UI_COMPONENTS.barChartCard,
  GENERATIVE_UI_COMPONENTS.lineAreaChartCard,
  GENERATIVE_UI_COMPONENTS.metricComparisonChartCard,
  GENERATIVE_UI_COMPONENTS.donutChartCard,
  GENERATIVE_UI_COMPONENTS.insightTable,
  GENERATIVE_UI_COMPONENTS.policyBreachCard,
  GENERATIVE_UI_COMPONENTS.warehouseStatusCard,
] as const;

export type DashboardVisualType = (typeof DASHBOARD_VISUAL_TYPES)[number];

export const DASHBOARD_VISUAL_PRIORITY: Record<DashboardVisualType, number> = {
  riskNarrativeCard: 0,
  kpiStrip: 1,
  barChartCard: 2,
  lineAreaChartCard: 2,
  metricComparisonChartCard: 2,
  donutChartCard: 3,
  policyBreachCard: 3,
  insightTable: 4,
  warehouseStatusCard: 5,
};
