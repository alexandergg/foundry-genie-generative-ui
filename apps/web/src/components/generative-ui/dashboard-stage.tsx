"use client";

import { useEffect, useSyncExternalStore } from "react";
import { DatabricksGenieMark } from "../databricks-genie-mark";
import { BarChartCard } from "./bar-chart-card";
import { DonutChartCard } from "./donut-chart-card";
import { InsightTable } from "./insight-table";
import { KpiStrip } from "./kpi-strip";
import { LineAreaChartCard } from "./line-area-chart-card";
import { MetricComparisonChartCard } from "./metric-comparison-chart-card";
import { RiskNarrativeCard } from "./risk-narrative-card";
import { WarehouseStatusCard } from "./warehouse-status-card";
import type {
  BarChartCardProps,
  DonutChartCardProps,
  InsightTableProps,
  KpiStripProps,
  LineAreaChartCardProps,
  MetricComparisonChartCardProps,
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
  | { id: string; type: "warehouseStatusCard"; props: WarehouseStatusCardProps };

type DashboardState = {
  phase: "idle" | "loading" | "ready";
  plan?: VisualizationPlanProps;
  visuals: DashboardVisual[];
};

const visualPriority: Record<DashboardVisual["type"], number> = {
  riskNarrativeCard: 0,
  kpiStrip: 1,
  barChartCard: 2,
  lineAreaChartCard: 2,
  metricComparisonChartCard: 2,
  donutChartCard: 3,
  insightTable: 4,
  warehouseStatusCard: 5,
};

let dashboardState: DashboardState = { phase: "idle", visuals: [] };
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot() {
  return dashboardState;
}

export function setDashboardLoading(plan?: VisualizationPlanProps) {
  dashboardState = { phase: "loading", plan, visuals: [] };
  emit();
}

function publishDashboardVisual(visual: DashboardVisual) {
  const withoutCurrent = dashboardState.visuals.filter((item) => item.id !== visual.id);
  dashboardState = {
    ...dashboardState,
    phase: "ready",
    visuals: [...withoutCurrent, visual].sort((a, b) => visualPriority[a.type] - visualPriority[b.type]),
  };
  emit();
}

function renderVisual(visual: DashboardVisual) {
  switch (visual.type) {
    case "kpiStrip":
      return <KpiStrip {...visual.props} />;
    case "barChartCard":
      return <BarChartCard {...visual.props} />;
    case "lineAreaChartCard":
      return <LineAreaChartCard {...visual.props} />;
    case "donutChartCard":
      return <DonutChartCard {...visual.props} />;
    case "metricComparisonChartCard":
      return <MetricComparisonChartCard {...visual.props} />;
    case "insightTable":
      return <InsightTable {...visual.props} />;
    case "riskNarrativeCard":
      return <RiskNarrativeCard {...visual.props} />;
    case "warehouseStatusCard":
      return <WarehouseStatusCard {...visual.props} />;
  }
}

function SkeletonVisuals() {
  return (
    <div className="dashboard-skeletons" aria-label="Generating visualizations">
      <div className="skeleton-card skeleton-chart data-orchestration">
        <div className="query-beam" />
        <div className="skeleton-line short" />
        <div className="skeleton-bars">
          <span style={{ height: "36%" }} />
          <span style={{ height: "58%" }} />
          <span style={{ height: "82%" }} />
          <span style={{ height: "52%" }} />
          <span style={{ height: "70%" }} />
        </div>
      </div>
      <div className="skeleton-card skeleton-table">
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
      </div>
    </div>
  );
}

export function DashboardStage() {
  const state = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  const hasVisuals = state.visuals.length > 0;

  return (
    <section className="dashboard-card" aria-label="Generative visualization panel">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">Generative canvas</p>
          <h2>Visual insights</h2>
        </div>
        <span className={`dashboard-state ${state.phase}`}>{state.phase === "ready" ? "ready" : state.phase === "loading" ? "generating" : "waiting"}</span>
      </div>

      {!hasVisuals && state.phase === "idle" && (
        <div className="dashboard-placeholder">
          <div className="genie-orchestrator" aria-hidden="true">
            <span className="orbit orbit-one" />
            <span className="orbit orbit-two" />
            <span className="orbit-dot dot-one" />
            <span className="orbit-dot dot-two" />
            <DatabricksGenieMark animated />
          </div>
          <h3>Ask a question to create the dashboard</h3>
          <p>Genie will turn governed warehouse results into live KPIs, charts and executive tables.</p>
          <div className="startup-steps" aria-hidden="true">
            <span>Governed query</span>
            <span>Genie reasoning</span>
            <span>Visual canvas</span>
          </div>
        </div>
      )}

      {!hasVisuals && state.phase === "loading" && (
        <div className="dashboard-loading">
          <SkeletonVisuals />
        </div>
      )}

      {hasVisuals && (
        <div className="dashboard-visuals">
          {state.visuals.map((visual) => <div className="dashboard-visual" key={visual.id}>{renderVisual(visual)}</div>)}
        </div>
      )}
    </section>
  );
}

export function DashboardVisualBridge({ visual }: { visual: DashboardVisual }) {
  useEffect(() => {
    publishDashboardVisual(visual);
  }, [visual]);

  return <div className="chat-visual-sent">Visualization updated in the central panel.</div>;
}

export function DashboardPlanBridge({ plan }: { plan: VisualizationPlanProps }) {
  useEffect(() => {
    setDashboardLoading(plan);
  }, [plan]);

  return <div className="chat-visual-sent">Preparing the visualization in the central panel…</div>;
}

export function DashboardToolStatusBridge({ name, status }: { name: string; status: string }) {
  useEffect(() => {
    if (status !== "complete") {
      setDashboardLoading({
        approach: `Running ${name}`,
        technology: "Azure AI Foundry + Databricks Genie + AG-UI",
        key_elements: ["governed query", "normalization", "visual rendering"],
      });
    }
  }, [name, status]);

  return <div className="chat-visual-sent">{name}: {status}</div>;
}
