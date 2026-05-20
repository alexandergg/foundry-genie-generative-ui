"use client";

import { useEffect, useSyncExternalStore } from "react";
import { DatabricksGenieMark } from "../databricks-genie-mark";
import { BarChartCard } from "./bar-chart-card";
import { getDashboardSnapshot, publishDashboardVisual, setDashboardPlanning, subscribeDashboard } from "./dashboard-store";
import { getProcessSnapshot, subscribeProcess } from "./process-store";
import type { DashboardVisual } from "./dashboard-store";
import { DonutChartCard } from "./donut-chart-card";
import { InsightTable } from "./insight-table";
import { KpiStrip } from "./kpi-strip";
import { LineAreaChartCard } from "./line-area-chart-card";
import { MetricComparisonChartCard } from "./metric-comparison-chart-card";
import { PolicyBreachCard } from "./policy-breach-card";
import { RiskNarrativeCard } from "./risk-narrative-card";
import { StatusTimeline, formatDashboardPhase } from "./status-timeline";
import { WarehouseStatusCard } from "./warehouse-status-card";
import type { VisualizationPlanProps } from "./types";

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
    case "policyBreachCard":
      return <PolicyBreachCard {...visual.props} />;
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
  const state = useSyncExternalStore(subscribeDashboard, getDashboardSnapshot, getDashboardSnapshot);
  const process = useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot);
  const hasVisuals = state.visuals.length > 0;

  return (
    <section className="dashboard-card" aria-label="Generative visualization panel">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">Generative canvas</p>
          <h2>Visual insights</h2>
        </div>
        <span className={`dashboard-state ${state.phase}`}>{formatDashboardPhase(state.phase)}</span>
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

      {!hasVisuals && state.phase !== "idle" && (
        <div className="dashboard-loading">
          <StatusTimeline events={process.steps} />
          <SkeletonVisuals />
        </div>
      )}

      {hasVisuals && (
        <div className="dashboard-visuals">
          <StatusTimeline events={process.steps} />
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
    setDashboardPlanning(plan);
  }, [plan]);

  return <div className="chat-visual-sent">Preparing the visualization in the central panel…</div>;
}
