import { DASHBOARD_VISUAL_PRIORITY } from "./registry";
import type {
  BarChartCardProps,
  DonutChartCardProps,
  InsightTableProps,
  KpiStripProps,
  LineAreaChartCardProps,
  MetricComparisonChartCardProps,
  PolicyBreachCardProps,
  RiskNarrativeCardProps,
  VisualizationPlanProps,
  WarehouseStatusCardProps,
} from "./types";

export type DashboardVisual =
  | { id: string; type: "kpiStrip"; props: KpiStripProps }
  | { id: string; type: "barChartCard"; props: BarChartCardProps }
  | { id: string; type: "lineAreaChartCard"; props: LineAreaChartCardProps }
  | { id: string; type: "donutChartCard"; props: DonutChartCardProps }
  | { id: string; type: "metricComparisonChartCard"; props: MetricComparisonChartCardProps }
  | { id: string; type: "insightTable"; props: InsightTableProps }
  | { id: string; type: "riskNarrativeCard"; props: RiskNarrativeCardProps }
  | { id: string; type: "warehouseStatusCard"; props: WarehouseStatusCardProps }
  | { id: string; type: "policyBreachCard"; props: PolicyBreachCardProps };

export type DashboardPhase = "idle" | "planning" | "ready";

export type DashboardState = {
  phase: DashboardPhase;
  plan?: VisualizationPlanProps;
  visuals: DashboardVisual[];
};

let dashboardState: DashboardState = { phase: "idle", visuals: [] };
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

export function subscribeDashboard(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getDashboardSnapshot() {
  return dashboardState;
}

export function setDashboardPlanning(plan?: VisualizationPlanProps) {
  dashboardState = { phase: "planning", plan, visuals: [] };
  emit();
}

export function publishDashboardVisual(visual: DashboardVisual) {
  const withoutCurrent = dashboardState.visuals.filter((item) => item.id !== visual.id);
  dashboardState = {
    ...dashboardState,
    phase: "ready",
    visuals: [...withoutCurrent, visual].sort(
      (a, b) => DASHBOARD_VISUAL_PRIORITY[a.type] - DASHBOARD_VISUAL_PRIORITY[b.type],
    ),
  };
  emit();
}
